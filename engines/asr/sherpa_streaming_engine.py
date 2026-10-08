from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np

from app.domain.models import AudioChunk, TranscriptSegment
from app.domain.ports import StreamingASREngine


class SherpaNemotronStreamingASR(StreamingASREngine):
    """Streaming ASR adapter backed by sherpa-onnx Nemotron-3.5."""

    def __init__(
        self,
        model_dir: str,
        num_threads: int = 4,
        provider: str = "cpu",
        local_only: bool = True,
    ) -> None:
        import sherpa_onnx

        path = Path(model_dir)
        if local_only and not path.exists():
            raise FileNotFoundError(f"Local Sherpa model not found: {path}")

        required = {
            "encoder.int8.onnx": path / "encoder.int8.onnx",
            "decoder.int8.onnx": path / "decoder.int8.onnx",
            "joiner.int8.onnx": path / "joiner.int8.onnx",
            "tokens.txt": path / "tokens.txt",
        }
        missing = [name for name, item in required.items() if not item.is_file()]
        if missing:
            raise FileNotFoundError(
                f"Sherpa model is incomplete; missing: {', '.join(missing)}"
            )

        self._recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(required["tokens.txt"]),
            encoder=str(required["encoder.int8.onnx"]),
            decoder=str(required["decoder.int8.onnx"]),
            joiner=str(required["joiner.int8.onnx"]),
            num_threads=num_threads,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=0.8,
            rule2_min_trailing_silence=0.45,
            rule3_min_utterance_length=20.0,
            provider=provider,
            debug=False,
        )
        self._stream = None
        self._last_text = ""
        self._utterance_started_at = 0.0

    @staticmethod
    def _samples(chunk: AudioChunk) -> np.ndarray:
        audio = np.frombuffer(chunk.samples, dtype=np.float32)
        channels = max(1, chunk.channels)
        if channels > 1:
            usable = (audio.size // channels) * channels
            audio = audio[:usable].reshape(-1, channels).mean(axis=1)
        return np.ascontiguousarray(audio, dtype=np.float32)

    @staticmethod
    def _language(result) -> str | None:
        for name in ("language", "lang", "language_code"):
            value = getattr(result, name, None)
            if value:
                return str(value).split("-")[0].lower()
        return None

    def start_stream(self) -> None:
        self._stream = self._recognizer.create_stream()
        self._last_text = ""
        self._utterance_started_at = 0.0

    def _decode(self, chunk_timestamp: float) -> list[TranscriptSegment]:
        if self._stream is None:
            return []

        results: list[TranscriptSegment] = []
        while self._recognizer.is_ready(self._stream):
            self._recognizer.decode_stream(self._stream)

        result = self._recognizer.get_result_all(self._stream)
        text = (getattr(result, "text", "") or "").strip()
        if text and text != self._last_text:
            if not self._utterance_started_at:
                self._utterance_started_at = chunk_timestamp
            self._last_text = text
            results.append(
                TranscriptSegment(
                    text=text,
                    start=self._utterance_started_at,
                    end=chunk_timestamp,
                    language_code=self._language(result),
                    confidence=None,
                    is_final=False,
                )
            )
        return results

    def accept_audio(self, chunk: AudioChunk) -> Iterable[TranscriptSegment]:
        if self._stream is None:
            self.start_stream()

        self._stream.accept_waveform(chunk.sample_rate, self._samples(chunk))
        results = self._decode(chunk.timestamp)

        if self._recognizer.is_endpoint(self._stream):
            result = self._recognizer.get_result_all(self._stream)
            text = (getattr(result, "text", "") or "").strip()
            if text:
                results.append(
                    TranscriptSegment(
                        text=text,
                        start=self._utterance_started_at or chunk.timestamp,
                        end=chunk.timestamp,
                        language_code=self._language(result),
                        confidence=None,
                        is_final=True,
                    )
                )
                # Mark endpoint by resetting the stream after the final partial.
                self._recognizer.reset(self._stream)
                self._last_text = ""
                self._utterance_started_at = 0.0
        return results

    def finish_stream(self) -> Iterable[TranscriptSegment]:
        if self._stream is None:
            return []

        self._stream.input_finished()
        while self._recognizer.is_ready(self._stream):
            self._recognizer.decode_stream(self._stream)

        result = self._recognizer.get_result_all(self._stream)
        text = (getattr(result, "text", "") or "").strip()
        self._stream = None
        self._last_text = ""
        if not text:
            return []
        return [
            TranscriptSegment(
                text=text,
                start=self._utterance_started_at,
                end=self._utterance_started_at,
                language_code=self._language(result),
                confidence=None,
            )
        ]

    def transcribe(self, chunks: Iterable[AudioChunk]) -> Iterable[TranscriptSegment]:
        """Compatibility path for deterministic callers."""
        self.start_stream()
        results: list[TranscriptSegment] = []
        for chunk in chunks:
            results.extend(self.accept_audio(chunk))
        results.extend(self.finish_stream())
        return results

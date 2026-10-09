from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np

from app.domain.models import AudioChunk, TranscriptSegment
from app.domain.ports import ASRRefiner


class FasterWhisperRefiner(ASRRefiner):
    """High-accuracy local Whisper pass for completed streaming utterances."""

    def __init__(
        self,
        model_dir: str,
        num_threads: int = 4,
        local_only: bool = True,
    ) -> None:
        from faster_whisper import WhisperModel

        path = Path(model_dir)
        if local_only and not path.exists():
            raise FileNotFoundError(f"Local Whisper refinement model not found: {path}")

        required = (
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.txt",
            "preprocessor_config.json",
        )
        missing = [name for name in required if not (path / name).is_file()]
        if missing:
            raise FileNotFoundError(
                f"Whisper refinement model is incomplete; missing: {', '.join(missing)}"
            )

        self._model = WhisperModel(
            str(path),
            device="cpu",
            compute_type="int8",
            cpu_threads=num_threads,
            num_workers=1,
            local_files_only=local_only,
        )

    @staticmethod
    def _audio(chunks: Iterable[AudioChunk]) -> np.ndarray:
        arrays: list[np.ndarray] = []
        sample_rate = 16000
        for chunk in chunks:
            if not chunk.samples:
                continue
            audio = np.frombuffer(chunk.samples, dtype=np.float32)
            channels = max(1, chunk.channels)
            if channels > 1:
                usable = (audio.size // channels) * channels
                audio = audio[:usable].reshape(-1, channels).mean(axis=1)
            if audio.size:
                arrays.append(np.ascontiguousarray(audio, dtype=np.float32))
                sample_rate = chunk.sample_rate
        if not arrays:
            return np.empty(0, dtype=np.float32)
        # The application capture path is 16 kHz. Keep the explicit sample-rate
        # contract here so future capture backends can validate it at the boundary.
        if sample_rate != 16000:
            raise ValueError(f"Whisper refinement requires 16000 Hz, got {sample_rate}")
        return np.concatenate(arrays).astype(np.float32, copy=False)

    def refine(
        self,
        chunks: Iterable[AudioChunk],
        language_code: str,
    ) -> Iterable[TranscriptSegment]:
        audio = self._audio(chunks)
        if audio.size == 0:
            return []

        segments, _info = self._model.transcribe(
            audio,
            language=language_code,
            task="transcribe",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            # The streaming endpoint already delimits the phrase. A second VAD pass
            # could discard short words during fast speech, so keep the complete audio.
            vad_filter=False,
        )

        output: list[TranscriptSegment] = []
        for segment in segments:
            text = (segment.text or "").strip()
            if not text:
                continue
            output.append(
                TranscriptSegment(
                    text=text,
                    start=float(segment.start),
                    end=float(segment.end),
                    language_code=language_code,
                    confidence=None,
                    is_final=True,
                )
            )
        return output

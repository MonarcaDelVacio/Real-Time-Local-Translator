from __future__ import annotations

from collections.abc import Callable

from app.domain.models import AudioChunk, TranslationSegment
from app.domain.ports import ASREngine, AudioSource, TranslationEngine, VoiceActivityDetector


class TranslationPipeline:
    """Turns system-audio chunks into bounded translated utterance events."""

    def __init__(
        self,
        source: AudioSource,
        vad: VoiceActivityDetector,
        asr: ASREngine,
        translator: TranslationEngine,
        target_language: str = "es",
        silence_chunks: int = 8,
        max_utterance_seconds: float = 18.0,
        max_buffer_chunks: int = 160,
    ) -> None:
        if silence_chunks < 1 or max_utterance_seconds <= 0 or max_buffer_chunks < 1:
            raise ValueError("Invalid pipeline limits")
        self.source = source
        self.vad = vad
        self.asr = asr
        self.translator = translator
        self.target_language = target_language
        self.silence_chunks = silence_chunks
        self.max_utterance_seconds = max_utterance_seconds
        self.max_buffer_chunks = max_buffer_chunks
        self._speech: list[AudioChunk] = []
        self._silence = 0

    def _buffer_duration(self) -> float:
        if not self._speech:
            return 0.0
        first = self._speech[0]
        bytes_per_sample = 4
        frames = sum(len(c.samples) for c in self._speech) / (
            bytes_per_sample * max(1, first.channels)
        )
        return frames / max(1, first.sample_rate)

    def process_chunk(self, chunk: AudioChunk) -> list[TranslationSegment]:
        if self.vad.is_speech(chunk):
            self._speech.append(chunk)
            self._silence = 0
            if (
                len(self._speech) >= self.max_buffer_chunks
                or self._buffer_duration() >= self.max_utterance_seconds
            ):
                return self.flush()
            return []

        if not self._speech:
            return []

        self._silence += 1
        if self._silence < self.silence_chunks:
            return []
        return self.flush()

    def flush(
        self,
        on_error: Callable[[Exception], None] | None = None,
    ) -> list[TranslationSegment]:
        if not self._speech:
            return []

        chunks, self._speech = self._speech, []
        self._silence = 0
        results: list[TranslationSegment] = []

        try:
            segments = self.asr.transcribe(chunks)
            for segment in segments:
                if not segment.text.strip():
                    continue
                try:
                    results.append(self.translator.translate(segment, self.target_language))
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
                    else:
                        raise
        except Exception as exc:
            if on_error is not None:
                on_error(exc)
            else:
                raise
        return results

    def run(
        self,
        on_translation: Callable[[TranslationSegment], None],
        stop_requested: Callable[[], bool],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.source.start()
        try:
            while not stop_requested():
                try:
                    chunk = self.source.read()
                    for result in self.process_chunk(chunk):
                        on_translation(result)
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
                    else:
                        raise

            for result in self.flush(on_error):
                on_translation(result)
        finally:
            self.source.stop()
            self._speech.clear()
            self._silence = 0

from __future__ import annotations

from collections.abc import Callable, Iterable

from app.domain.models import AudioChunk, TranslationSegment, TranscriptSegment
from app.domain.ports import (
    ASREngine,
    AudioSource,
    StreamingASREngine,
    TranslationEngine,
    VoiceActivityDetector,
)


class TranslationPipeline:
    """Translate either chunked offline ASR or true streaming ASR."""

    def __init__(
        self,
        source: AudioSource,
        vad: VoiceActivityDetector,
        asr: ASREngine,
        translator: TranslationEngine,
        target_language: str = "es",
        silence_chunks: int = 4,
        max_utterance_seconds: float = 20.0,
        max_buffer_chunks: int = 400,
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
        frames = sum(len(c.samples) for c in self._speech) / (
            4 * max(1, first.channels)
        )
        return frames / max(1, first.sample_rate)

    def _take_speech(self) -> list[AudioChunk]:
        chunks, self._speech = self._speech, []
        self._silence = 0
        return chunks

    def _collect_utterance(self, chunk: AudioChunk) -> list[AudioChunk] | None:
        if self.vad.is_speech(chunk):
            self._speech.append(chunk)
            self._silence = 0
            if (
                len(self._speech) >= self.max_buffer_chunks
                or self._buffer_duration() >= self.max_utterance_seconds
            ):
                return self._take_speech()
            return None
        if not self._speech:
            return None
        self._silence += 1
        if self._silence < self.silence_chunks:
            return None
        return self._take_speech()

    def _resolve_language(self, segment: TranscriptSegment) -> TranscriptSegment:
        if segment.language_code:
            return segment
        fallback = "en" if self.target_language == "es" else "es"
        return TranscriptSegment(
            segment.text,
            segment.start,
            segment.end,
            fallback,
            segment.confidence,
            segment.is_final,
        )

    def _translate_segments(
        self,
        segments: Iterable[TranscriptSegment],
        on_translation: Callable[[TranslationSegment], None],
        on_error: Callable[[Exception], None] | None,
    ) -> None:
        for segment in segments:
            if not segment.text.strip():
                continue
            try:
                translated = self.translator.translate(
                    self._resolve_language(segment), self.target_language
                )
                on_translation(translated)
            except Exception as exc:
                if on_error is not None:
                    on_error(exc)
                else:
                    raise

    def _translate_chunks(
        self,
        chunks: list[AudioChunk],
        on_error: Callable[[Exception], None] | None = None,
    ) -> list[TranslationSegment]:
        if not chunks:
            return []
        results: list[TranslationSegment] = []
        try:
            self._translate_segments(
                self.asr.transcribe(chunks), results.append, on_error
            )
        except Exception as exc:
            if on_error is not None:
                on_error(exc)
            else:
                raise
        return results

    def process_chunk(self, chunk: AudioChunk) -> list[TranslationSegment]:
        ready = self._collect_utterance(chunk)
        if ready is None:
            return []
        return self._translate_chunks(ready)

    def flush(
        self,
        on_error: Callable[[Exception], None] | None = None,
    ) -> list[TranslationSegment]:
        return self._translate_chunks(self._take_speech(), on_error)

    def _run_streaming(
        self,
        on_translation: Callable[[TranslationSegment], None],
        stop_requested: Callable[[], bool],
        on_error: Callable[[Exception], None] | None,
    ) -> None:
        engine = self.asr
        if not isinstance(engine, StreamingASREngine):
            raise TypeError("Streaming pipeline requires a streaming ASR engine")
        engine.start_stream()
        try:
            while not stop_requested():
                chunk = self.source.read()
                self._translate_segments(
                    engine.accept_audio(chunk), on_translation, on_error
                )
            self._translate_segments(
                engine.finish_stream(), on_translation, on_error
            )
        except Exception as exc:
            if on_error is not None:
                on_error(exc)
            else:
                raise

    def run(
        self,
        on_translation: Callable[[TranslationSegment], None],
        stop_requested: Callable[[], bool],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.source.start()
        try:
            if isinstance(self.asr, StreamingASREngine):
                self._run_streaming(on_translation, stop_requested, on_error)
                return

            while not stop_requested():
                try:
                    chunk = self.source.read()
                    ready = self._collect_utterance(chunk)
                    if ready is not None:
                        for result in self._translate_chunks(ready, on_error):
                            on_translation(result)
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
                    else:
                        raise

            for result in self._translate_chunks(self._take_speech(), on_error):
                on_translation(result)
        finally:
            self.source.stop()
            self._speech.clear()
            self._silence = 0

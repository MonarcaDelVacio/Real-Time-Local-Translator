from __future__ import annotations

from collections.abc import Callable, Iterable

from app.domain.models import AudioChunk, TranslationSegment, TranscriptSegment
from app.domain.ports import (
    ASREngine,
    ASRRefiner,
    AudioSource,
    StreamingASREngine,
    TranslationEngine,
    VoiceActivityDetector,
)


class TranslationPipeline:
    """Translate chunked offline ASR or stabilized true streaming ASR."""

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
        refiner: ASRRefiner | None = None,
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
        self.refiner = refiner
        self._speech: list[AudioChunk] = []
        self._silence = 0
        self._stream_audio_truncated = False

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

    def _append_stream_audio(self, chunk: AudioChunk) -> None:
        """Bound retained audio so a missing endpoint cannot grow memory forever."""
        self._speech.append(chunk)
        while self._speech and (
            len(self._speech) > self.max_buffer_chunks
            or self._buffer_duration() > self.max_utterance_seconds
        ):
            self._speech.pop(0)
            self._stream_audio_truncated = True

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
        finals_only: bool = False,
    ) -> None:
        for segment in segments:
            if not segment.text.strip() or (finals_only and not segment.is_final):
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
        import queue
        import threading

        engine = self.asr
        if not isinstance(engine, StreamingASREngine):
            raise TypeError("Streaming pipeline requires a streaming ASR engine")

        source_language = "en" if self.target_language == "es" else "es"
        set_source_language = getattr(engine, "set_source_language", None)
        if set_source_language is not None:
            set_source_language(source_language)

        # Audio capture runs independently from ASR/Whisper. Refinement can take
        # several seconds, so it must not stop the device from being read.
        audio_queue: queue.Queue = queue.Queue(maxsize=max(128, self.max_buffer_chunks * 2))
        sentinel = object()
        producer_stop = threading.Event()
        capture_errors: list[Exception] = []

        def capture_audio() -> None:
            try:
                while not producer_stop.is_set() and not stop_requested():
                    chunk = self.source.read()
                    while True:
                        try:
                            audio_queue.put(chunk, timeout=0.1)
                            break
                        except queue.Full:
                            # Back-pressure is bounded. On abnormal consumer
                            # shutdown, allow the producer to exit cleanly.
                            if producer_stop.is_set():
                                return
            except Exception as exc:
                capture_errors.append(exc)
            finally:
                while True:
                    try:
                        audio_queue.put(sentinel, timeout=0.1)
                        break
                    except queue.Full:
                        if producer_stop.is_set():
                            return

        engine.start_stream()
        producer = threading.Thread(
            target=capture_audio,
            name="RTL-Audio-Capture",
            daemon=True,
        )
        producer.start()
        try:
            while True:
                try:
                    item = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    if not producer.is_alive():
                        break
                    continue
                if item is sentinel:
                    break

                chunk = item
                segments = list(engine.accept_audio(chunk))
                self._append_stream_audio(chunk)

                for segment in segments:
                    if segment.is_final:
                        audio = list(self._speech)
                        truncated = self._stream_audio_truncated
                        self._speech.clear()
                        self._stream_audio_truncated = False
                        final_segments = [segment]
                        # If the user is stopping, preserve the fast shutdown
                        # path and use the already-decoded streaming transcript.
                        if (
                            self.refiner is not None
                            and not truncated
                            and not stop_requested()
                            and not capture_errors
                        ):
                            try:
                                refined = list(self.refiner.refine(audio, source_language))
                                if refined:
                                    final_segments = refined
                            except Exception as exc:
                                if on_error is not None:
                                    on_error(exc)
                        self._translate_segments(final_segments, on_translation, on_error)
                    elif segment.text.strip():
                        # Translate each updated streaming hypothesis immediately.
                        # The UI treats non-final segments as a replaceable live
                        # preview, so cumulative hypotheses do not pollute history.
                        self._translate_segments(
                            [segment], on_translation, on_error
                        )

            stopping = stop_requested() or bool(capture_errors)
            finals = list(engine.finish_stream())
            if (
                self._speech
                and self.refiner is not None
                and not stopping
                and not self._stream_audio_truncated
            ):
                try:
                    refined = list(self.refiner.refine(self._speech, source_language))
                    if refined:
                        finals = refined
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
            self._speech.clear()
            self._stream_audio_truncated = False
            self._translate_segments(finals, on_translation, on_error)

            if capture_errors and on_error is not None:
                on_error(capture_errors[0])
        except Exception as exc:
            if on_error is not None:
                on_error(exc)
            else:
                raise
        finally:
            producer_stop.set()
            producer.join(timeout=2.0)

    def run(
        self,
        on_translation: Callable[[TranslationSegment], None],
        stop_requested: Callable[[], bool],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        try:
            # Some audio backends may partially initialize a device before raising.
            self.source.start()
            if isinstance(self.asr, StreamingASREngine):
                self._run_streaming(on_translation, stop_requested, on_error)
                return

            while not stop_requested():
                # Device/read failures are fatal for this session. Catching them
                # and immediately looping can create a tight infinite error loop.
                chunk = self.source.read()
                ready = self._collect_utterance(chunk)
                if ready is not None:
                    for result in self._translate_chunks(ready, on_error):
                        on_translation(result)

            for result in self._translate_chunks(self._take_speech(), on_error):
                on_translation(result)
        finally:
            import sys

            active_error = sys.exc_info()[0] is not None
            try:
                self.source.stop()
            except Exception as stop_error:
                # Do not mask the original capture/recognition error with a
                # secondary device-cleanup failure.
                if on_error is not None:
                    on_error(stop_error)
                elif not active_error:
                    raise
            finally:
                self._speech.clear()
                self._silence = 0
                self._stream_audio_truncated = False

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
        on_transcript: Callable[[TranscriptSegment], None] | None = None,
    ) -> None:
        for segment in segments:
            if not segment.text.strip() or (finals_only and not segment.is_final):
                continue
            if segment.is_final and on_transcript is not None:
                try:
                    on_transcript(segment)
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
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
        on_transcript: Callable[[TranscriptSegment], None] | None = None,
    ) -> list[TranslationSegment]:
        if not chunks:
            return []
        results: list[TranslationSegment] = []
        try:
            self._translate_segments(
                self.asr.transcribe(chunks), results.append, on_error,
                on_transcript=on_transcript,
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
        on_transcript: Callable[[TranscriptSegment], None] | None = None,
    ) -> None:
        import queue
        import threading
        import time

        engine = self.asr
        if not isinstance(engine, StreamingASREngine):
            raise TypeError("Streaming pipeline requires a streaming ASR engine")

        source_language = "en" if self.target_language == "es" else "es"
        set_source_language = getattr(engine, "set_source_language", None)
        if set_source_language is not None:
            set_source_language(source_language)

        # Capture and streaming ASR must never wait for Whisper refinement.
        # Keep the device queue bounded to avoid latency growing without limit.
        audio_queue: queue.Queue = queue.Queue(maxsize=32)
        refinement_jobs: queue.Queue = queue.Queue(maxsize=4)
        refinement_results: queue.Queue = queue.Queue()
        sentinel = object()
        producer_stop = threading.Event()
        audio_discontinuity = threading.Event()
        capture_errors: list[Exception] = []
        pending_refinements = 0
        next_final_sequence = 0
        next_final_to_emit = 0
        completed_finals: dict[int, tuple[list[TranscriptSegment], Exception | None]] = {}
        deferred_preview: TranscriptSegment | None = None
        refiner_thread: threading.Thread | None = None
        refiner_shutdown = False

        def capture_audio() -> None:
            try:
                while not producer_stop.is_set() and not stop_requested():
                    chunk = self.source.read()
                    try:
                        audio_queue.put(chunk, timeout=0.02)
                    except queue.Full:
                        # Publish the discontinuity before replacing a queued chunk.
                        # The consumer checks this flag before decoding its next item.
                        audio_discontinuity.set()
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            pass
                        try:
                            audio_queue.put_nowait(chunk)
                        except queue.Full:
                            pass
            except Exception as exc:
                capture_errors.append(exc)
            finally:
                while not producer_stop.is_set():
                    try:
                        audio_queue.put(sentinel, timeout=0.1)
                        break
                    except queue.Full:
                        continue

        def refine_worker() -> None:
            while True:
                job = refinement_jobs.get()
                if job is sentinel:
                    return
                sequence, audio, language, fallback = job
                error = None
                try:
                    refined = list(self.refiner.refine(audio, language))
                    if not refined:
                        refined = [fallback]
                except Exception as exc:
                    refined = [fallback]
                    error = exc
                refinement_results.put((sequence, refined, error))

        if self.refiner is not None:
            refiner_thread = threading.Thread(
                target=refine_worker,
                name="RTL-Whisper-Refinement",
                daemon=True,
            )
            refiner_thread.start()

        def emit_ready_finals() -> None:
            nonlocal next_final_to_emit, deferred_preview
            while next_final_to_emit in completed_finals:
                segments, refinement_error = completed_finals.pop(next_final_to_emit)
                if refinement_error is not None and on_error is not None:
                    on_error(refinement_error)
                self._translate_segments(
                    segments, on_translation, on_error,
                    finals_only=True, on_transcript=on_transcript,
                )
                next_final_to_emit += 1
            # The UI currently owns one provisional entry. Defer later previews
            # until all outstanding refinements are resolved so a late final
            # cannot accidentally replace a newer utterance's preview.
            if pending_refinements == 0 and deferred_preview is not None:
                preview, deferred_preview = deferred_preview, None
                self._translate_segments([preview], on_translation, on_error)

        def drain_refinement_results() -> None:
            nonlocal pending_refinements
            while True:
                try:
                    sequence, segments, error = refinement_results.get_nowait()
                except queue.Empty:
                    break
                pending_refinements = max(0, pending_refinements - 1)
                completed_finals[sequence] = (segments, error)
            emit_ready_finals()

        def schedule_final(segment: TranscriptSegment, audio: list[AudioChunk], truncated: bool) -> None:
            nonlocal next_final_sequence, pending_refinements
            sequence = next_final_sequence
            next_final_sequence += 1
            should_refine = (
                self.refiner is not None
                and audio
                and not truncated
                and not stop_requested()
                and not capture_errors
            )
            if should_refine:
                try:
                    refinement_jobs.put_nowait((sequence, audio, source_language, segment))
                    pending_refinements += 1
                except queue.Full:
                    # Under extreme backlog, keep the already-decoded final rather
                    # than block the ASR consumer and lose more live audio.
                    completed_finals[sequence] = ([segment], None)
            else:
                completed_finals[sequence] = ([segment], None)
            drain_refinement_results()
            emit_ready_finals()

        engine.start_stream()
        producer = threading.Thread(
            target=capture_audio,
            name="RTL-Audio-Capture",
            daemon=True,
        )
        producer.start()
        last_preview_at = 0.0
        last_preview_text = ""
        try:
            while True:
                drain_refinement_results()
                try:
                    item = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    if not producer.is_alive():
                        break
                    continue
                if item is sentinel:
                    break

                if audio_discontinuity.is_set():
                    audio_discontinuity.clear()
                    engine.start_stream()
                    self._speech.clear()
                    self._stream_audio_truncated = False
                    last_preview_at = 0.0
                    last_preview_text = ""

                chunk = item
                segments = list(engine.accept_audio(chunk))
                self._append_stream_audio(chunk)

                for segment in segments:
                    if segment.is_final:
                        audio = list(self._speech)
                        truncated = self._stream_audio_truncated
                        self._speech.clear()
                        self._stream_audio_truncated = False
                        schedule_final(segment, audio, truncated)
                        last_preview_at = 0.0
                        last_preview_text = ""
                    elif segment.text.strip():
                        now = time.monotonic()
                        if segment.text != last_preview_text and now - last_preview_at >= 0.35:
                            last_preview_at = now
                            last_preview_text = segment.text
                            if pending_refinements:
                                deferred_preview = segment
                            else:
                                self._translate_segments([segment], on_translation, on_error)

            stopping = stop_requested() or bool(capture_errors)
            finals = list(engine.finish_stream())
            if finals:
                audio = list(self._speech)
                truncated = self._stream_audio_truncated
                self._speech.clear()
                self._stream_audio_truncated = False
                if (
                    self.refiner is not None
                    and audio
                    and not truncated
                    and not stopping
                    and not capture_errors
                ):
                    # Capture has ended, so this final tail can be refined here
                    # without risking loss of new audio from the device.
                    try:
                        refined = list(self.refiner.refine(audio, source_language))
                        if refined:
                            finals = refined
                    except Exception as exc:
                        if on_error is not None:
                            on_error(exc)
                for segment in finals:
                    schedule_final(segment, [], True)

            self._speech.clear()
            self._stream_audio_truncated = False

            if refiner_thread is not None:
                # Queue sentinel after all scheduled jobs, then drain completed
                # results in sequence order before returning from the session.
                refinement_jobs.put(sentinel)
                refiner_thread.join()
                refiner_shutdown = True
                drain_refinement_results()
                emit_ready_finals()

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
            if refiner_thread is not None and not refiner_shutdown:
                try:
                    refinement_jobs.put(sentinel, timeout=0.5)
                except queue.Full:
                    pass
                refiner_thread.join(timeout=2.0)

    def run(
        self,
        on_translation: Callable[[TranslationSegment], None],
        stop_requested: Callable[[], bool],
        on_error: Callable[[Exception], None] | None = None,
        on_transcript: Callable[[TranscriptSegment], None] | None = None,
    ) -> None:
        try:
            # Some audio backends may partially initialize a device before raising.
            self.source.start()
            if isinstance(self.asr, StreamingASREngine):
                self._run_streaming(on_translation, stop_requested, on_error, on_transcript)
                return

            while not stop_requested():
                # Device/read failures are fatal for this session. Catching them
                # and immediately looping can create a tight infinite error loop.
                chunk = self.source.read()
                ready = self._collect_utterance(chunk)
                if ready is not None:
                    for result in self._translate_chunks(ready, on_error, on_transcript):
                        on_translation(result)

            for result in self._translate_chunks(self._take_speech(), on_error, on_transcript):
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

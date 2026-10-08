from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

from app.domain.models import AudioChunk, TranslationSegment
from app.domain.ports import ASREngine, AudioSource, TranslationEngine, VoiceActivityDetector


class TranslationPipeline:
    """Turns system-audio chunks into translated utterance events.

    Audio capture is kept separate from the CPU-heavy ASR/translation work.
    This prevents the microphone/system-audio reader from stopping while
    Whisper is processing a previous utterance.
    """

    def __init__(
        self,
        source: AudioSource,
        vad: VoiceActivityDetector,
        asr: ASREngine,
        translator: TranslationEngine,
        target_language: str = "es",
        silence_chunks: int = 4,
        max_utterance_seconds: float = 7.0,
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

    def _translate_chunks(
        self,
        chunks: list[AudioChunk],
        on_error: Callable[[Exception], None] | None = None,
    ) -> list[TranslationSegment]:
        if not chunks:
            return []

        results: list[TranslationSegment] = []
        try:
            segments = self.asr.transcribe(chunks)
            for segment in segments:
                if not segment.text.strip():
                    continue
                try:
                    results.append(
                        self.translator.translate(segment, self.target_language)
                    )
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

    def process_chunk(self, chunk: AudioChunk) -> list[TranslationSegment]:
        """Process one chunk synchronously; kept for deterministic unit tests."""
        ready = self._collect_utterance(chunk)
        if ready is None:
            return []
        return self._translate_chunks(ready)

    def flush(
        self,
        on_error: Callable[[Exception], None] | None = None,
    ) -> list[TranslationSegment]:
        return self._translate_chunks(self._take_speech(), on_error)

    @staticmethod
    def _deliver_future(
        future: Future[list[TranslationSegment]],
        on_translation: Callable[[TranslationSegment], None],
        on_error: Callable[[Exception], None] | None,
    ) -> None:
        try:
            for result in future.result():
                on_translation(result)
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
        futures: list[Future[list[TranslationSegment]]] = []

        # One worker is intentional: ASR remains ordered and does not compete
        # with itself for all CPU cores, while capture continues uninterrupted.
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="translator") as executor:
            try:
                while not stop_requested():
                    try:
                        chunk = self.source.read()
                        ready = self._collect_utterance(chunk)
                        if ready is not None:
                            future = executor.submit(
                                self._translate_chunks, ready, on_error
                            )
                            future.add_done_callback(
                                lambda f: self._deliver_future(
                                    f, on_translation, on_error
                                )
                            )
                            futures.append(future)
                    except Exception as exc:
                        if on_error is not None:
                            on_error(exc)
                        else:
                            raise

                ready = self._take_speech()
                if ready:
                    future = executor.submit(self._translate_chunks, ready, on_error)
                    future.add_done_callback(
                        lambda f: self._deliver_future(f, on_translation, on_error)
                    )
                    futures.append(future)

                # Wait for all queued utterances before the worker thread exits.
                for future in futures:
                    future.result()
            finally:
                self.source.stop()
                self._speech.clear()
                self._silence = 0

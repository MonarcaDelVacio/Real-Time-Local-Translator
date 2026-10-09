from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.pipeline import TranslationPipeline
from app.domain.models import AudioChunk, TranscriptSegment, TranslationSegment
from app.domain.ports import ASREngine, AudioSource, TranslationEngine, VoiceActivityDetector


@dataclass
class FakeSource(AudioSource):
    chunks: list[AudioChunk]

    def start(self):
        pass

    def read(self):
        if not self.chunks:
            raise RuntimeError("done")
        return self.chunks.pop(0)

    def stop(self):
        pass


class FakeVAD(VoiceActivityDetector):
    def is_speech(self, chunk):
        return chunk.samples.startswith(b"speech")


class FakeASR(ASREngine):
    def transcribe(self, chunks):
        return [TranscriptSegment("hello", 0, 1, "en")]


class FakeTranslation(TranslationEngine):
    def translate(self, segment, target_language_code):
        return TranslationSegment(
            segment, "hola", target_language_code, datetime.now(timezone.utc)
        )


def test_pipeline_flushes_after_silence():
    p = TranslationPipeline(
        FakeSource([]), FakeVAD(), FakeASR(), FakeTranslation(), silence_chunks=2
    )
    assert p.process_chunk(AudioChunk(b"speech", 16000, 1, 0)) == []
    assert p.process_chunk(AudioChunk(b"silence", 16000, 1, 1)) == []
    result = p.process_chunk(AudioChunk(b"silence", 16000, 1, 2))
    assert result[0].translated_text == "hola"


def test_pipeline_flushes_when_utterance_reaches_limit():
    p = TranslationPipeline(
        FakeSource([]),
        FakeVAD(),
        FakeASR(),
        FakeTranslation(),
        max_utterance_seconds=0.05,
        max_buffer_chunks=10,
    )
    result = p.process_chunk(AudioChunk(b"speech" * 1000, 16000, 1, 0))
    assert result and result[0].translated_text == "hola"


def test_pipeline_reports_segment_error_and_keeps_running():
    errors = []

    class BrokenTranslation(FakeTranslation):
        def translate(self, segment, target_language_code):
            raise RuntimeError("translation unavailable")

    p = TranslationPipeline(
        FakeSource([]), FakeVAD(), FakeASR(), BrokenTranslation(), silence_chunks=1
    )
    p.process_chunk(AudioChunk(b"speech", 16000, 1, 0))
    p.run(
        lambda _: None,
        lambda: True,
        errors.append,
    )
    assert len(errors) == 1
    assert "translation unavailable" in str(errors[0])

def test_pipeline_stops_source_when_read_fails():
    import pytest

    class FailingSource(FakeSource):
        stopped = False

        def read(self):
            raise RuntimeError("audio device failed")

        def stop(self):
            self.stopped = True

    source = FailingSource([])
    p = TranslationPipeline(source, FakeVAD(), FakeASR(), FakeTranslation())
    with pytest.raises(RuntimeError, match="audio device failed"):
        p.run(lambda _: None, lambda: False)
    assert source.stopped

def test_streaming_capture_continues_while_whisper_refines():
    import time

    from app.domain.ports import ASRRefiner, StreamingASREngine

    class StreamingSource(FakeSource):
        read_count = 0

        def __init__(self, chunks):
            super().__init__(chunks)
            import threading
            self.refinement_finished = threading.Event()

        def read(self):
            if not self.chunks:
                # Keep the simulated live capture active until refinement has
                # started and completed; otherwise the test creates an
                # artificial end-of-stream error before refinement can run.
                self.refinement_finished.wait(timeout=2)
                raise RuntimeError("end of test audio")
            self.read_count += 1
            return self.chunks.pop(0)

    class StreamingEngine(StreamingASREngine):
        def start_stream(self):
            pass

        def accept_audio(self, chunk):
            return [
                TranscriptSegment("hello", 0, 1, "en", is_final=False),
                TranscriptSegment("hello", 0, 1, "en", is_final=True),
            ]

        def finish_stream(self):
            return []

        def transcribe(self, chunks):
            return []

    class SlowRefiner(ASRRefiner):
        def __init__(self, source):
            self.source = source
            self.capture_advanced_during_refinement = False

        def refine(self, chunks, language_code):
            # The capture producer should read ahead while this simulated
            # refinement is busy instead of losing the audio window.
            time.sleep(0.15)
            self.capture_advanced_during_refinement = self.source.read_count >= 5
            self.source.refinement_finished.set()
            return [TranscriptSegment("hello refined", 0, 1, language_code)]

    source = StreamingSource([
        AudioChunk(b"speech", 16000, 1, float(i)) for i in range(5)
    ])
    refiner = SlowRefiner(source)
    p = TranslationPipeline(source, FakeVAD(), StreamingEngine(), FakeTranslation(), refiner=refiner)
    results = []
    errors = []
    p.run(results.append, lambda: False, errors.append)

    final_results = [item for item in results if item.source.is_final]
    provisional_results = [item for item in results if not item.source.is_final]
    assert len(final_results) == 5
    assert provisional_results
    assert all(item.translated_text == "hola" for item in provisional_results)
    assert refiner.capture_advanced_during_refinement
    assert errors and "end of test audio" in str(errors[0])



def test_streaming_preview_resets_after_finalized_utterance():
    from app.domain.ports import StreamingASREngine

    class ThreeUtteranceEngine(StreamingASREngine):
        def start_stream(self):
            pass

        def accept_audio(self, chunk):
            if chunk.timestamp == 0:
                return [TranscriptSegment("hello", 0, 1, "en", is_final=False)]
            if chunk.timestamp == 1:
                return [TranscriptSegment("hello", 0, 1, "en", is_final=True)]
            return [TranscriptSegment("hello", 0, 1, "en", is_final=False)]

        def finish_stream(self):
            return []

        def transcribe(self, chunks):
            return []

    source = FakeSource([
        AudioChunk(b"speech", 16000, 1, float(i)) for i in range(3)
    ])
    pipeline = TranslationPipeline(
        source, FakeVAD(), ThreeUtteranceEngine(), FakeTranslation()
    )
    results = []
    errors = []
    pipeline.run(results.append, lambda: False, errors.append)

    provisional = [result for result in results if not result.source.is_final]
    finalized = [result for result in results if result.source.is_final]
    assert len(provisional) == 2
    assert len(finalized) == 1
    assert all(result.source.text == "hello" for result in provisional)

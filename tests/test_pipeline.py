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
        return chunk.samples == b"speech"


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

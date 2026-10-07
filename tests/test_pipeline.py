from dataclasses import dataclass
from app.application.pipeline import TranslationPipeline
from app.domain.models import AudioChunk, TranscriptSegment, TranslationSegment
from app.domain.ports import ASREngine, AudioSource, TranslationEngine, VoiceActivityDetector
from datetime import datetime, timezone

@dataclass
class FakeSource(AudioSource):
    chunks: list[AudioChunk]
    def start(self): pass
    def read(self): return self.chunks.pop(0)
    def stop(self): pass

class FakeVAD(VoiceActivityDetector):
    def is_speech(self, chunk): return chunk.samples == b"speech"

class FakeASR(ASREngine):
    def transcribe(self, chunks): return [TranscriptSegment("hello", 0, 1, "en")]

class FakeTranslation(TranslationEngine):
    def translate(self, segment, target_language_code): return TranslationSegment(segment, "hola", target_language_code, datetime.now(timezone.utc))

def test_pipeline_flushes_after_silence():
    p = TranslationPipeline(FakeSource([]), FakeVAD(), FakeASR(), FakeTranslation(), silence_chunks=2)
    assert p.process_chunk(AudioChunk(b"speech", 16000, 1, 0)) == []
    assert p.process_chunk(AudioChunk(b"silence", 16000, 1, 1)) == []
    result = p.process_chunk(AudioChunk(b"silence", 16000, 1, 2))
    assert result[0].translated_text == "hola"

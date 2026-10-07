from __future__ import annotations
from collections.abc import Callable
from app.domain.models import AudioChunk, TranslationSegment
from app.domain.ports import ASREngine, AudioSource, TranslationEngine, VoiceActivityDetector

class TranslationPipeline:
    """Turns streaming audio chunks into translated utterance events."""
    def __init__(self, source: AudioSource, vad: VoiceActivityDetector, asr: ASREngine, translator: TranslationEngine, target_language: str = "es", silence_chunks: int = 8) -> None:
        self.source, self.vad, self.asr, self.translator = source, vad, asr, translator
        self.target_language, self.silence_chunks = target_language, silence_chunks
        self._speech: list[AudioChunk] = []
        self._silence = 0

    def process_chunk(self, chunk: AudioChunk) -> list[TranslationSegment]:
        if self.vad.is_speech(chunk):
            self._speech.append(chunk); self._silence = 0
            return []
        if not self._speech: return []
        self._silence += 1
        if self._silence < self.silence_chunks: return []
        return self.flush()

    def flush(self) -> list[TranslationSegment]:
        if not self._speech: return []
        chunks, self._speech = self._speech, []
        self._silence = 0
        results: list[TranslationSegment] = []
        for segment in self.asr.transcribe(chunks):
            results.append(self.translator.translate(segment, self.target_language))
        return results

    def run(self, on_translation: Callable[[TranslationSegment], None], stop_requested: Callable[[], bool]) -> None:
        self.source.start()
        try:
            while not stop_requested():
                for result in self.process_chunk(self.source.read()): on_translation(result)
            for result in self.flush(): on_translation(result)
        finally:
            self.source.stop()

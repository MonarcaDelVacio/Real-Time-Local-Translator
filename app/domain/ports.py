"""Replaceable engine contracts."""
from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.domain.models import (
    AudioChunk,
    DetectedLanguage,
    TranscriptSegment,
    TranslationSegment,
)


class AudioSource(ABC):
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def read(self) -> AudioChunk: ...
    @abstractmethod
    def stop(self) -> None: ...


class VoiceActivityDetector(ABC):
    @abstractmethod
    def is_speech(self, chunk: AudioChunk) -> bool: ...


class ASREngine(ABC):
    @abstractmethod
    def transcribe(self, chunks: Iterable[AudioChunk]) -> Iterable[TranscriptSegment]: ...


class StreamingASREngine(ASREngine):
    """ASR engine that consumes live audio and returns partial/final text."""
    @abstractmethod
    def start_stream(self) -> None: ...
    @abstractmethod
    def accept_audio(self, chunk: AudioChunk) -> Iterable[TranscriptSegment]: ...
    @abstractmethod
    def finish_stream(self) -> Iterable[TranscriptSegment]: ...


class LanguageDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> DetectedLanguage: ...


class TranslationEngine(ABC):
    @abstractmethod
    def translate(
        self, segment: TranscriptSegment, target_language_code: str
    ) -> TranslationSegment: ...

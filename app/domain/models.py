"""Core data models shared by the translation pipeline."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    text: str
    start: float
    end: float
    language_code: str | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class DetectedLanguage:
    code: str | None
    confidence: float | None
    source: Literal["automatic", "manual", "unknown"]


@dataclass(frozen=True, slots=True)
class TranslationSegment:
    source: TranscriptSegment
    translated_text: str
    target_language_code: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AudioChunk:
    samples: bytes
    sample_rate: int
    channels: int
    timestamp: float

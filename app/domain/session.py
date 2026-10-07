"""Translation session model."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.domain.models import DetectedLanguage, TranslationSegment


@dataclass
class TranslationSession:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_language: DetectedLanguage | None = None
    target_language_code: str = "es"
    translations: list[TranslationSegment] = field(default_factory=list)
    active: bool = False
    error_count: int = 0

    def add_translation(self, segment: TranslationSegment) -> None:
        self.translations.append(segment)

    def register_error(self) -> None:
        self.error_count += 1

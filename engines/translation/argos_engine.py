from __future__ import annotations
from datetime import datetime, timezone
from app.domain.models import TranscriptSegment, TranslationSegment
from app.domain.ports import TranslationEngine

class ArgosTranslationEngine(TranslationEngine):
    """Offline Argos Translate adapter. Packages must be installed locally."""
    def translate(self, segment: TranscriptSegment, target_language_code: str) -> TranslationSegment:
        import argostranslate.translate
        source = segment.language_code or "en"
        text = argostranslate.translate.translate(segment.text, source, target_language_code)
        return TranslationSegment(segment, text, target_language_code, datetime.now(timezone.utc))

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.models import TranscriptSegment, TranslationSegment
from app.domain.ports import TranslationEngine


class ArgosTranslationEngine(TranslationEngine):
    """Offline Argos Translate adapter using only the configured local store."""

    def __init__(self) -> None:
        import argostranslate.translate as translate

        self._translate = translate

    def available(self, source_language_code: str, target_language_code: str) -> bool:
        if not source_language_code or source_language_code == target_language_code:
            return True
        try:
            return (
                self._translate.get_translation_from_codes(
                    source_language_code, target_language_code
                )
                is not None
            )
        except Exception:
            return False

    def translate(
        self,
        segment: TranscriptSegment,
        target_language_code: str,
    ) -> TranslationSegment:
        source = (segment.language_code or "").strip().lower()
        target = target_language_code.strip().lower()

        if not source:
            raise ValueError("ASR did not provide a detected source language.")
        if not target:
            raise ValueError("A target language is required.")
        if source == target:
            translated = segment.text
        elif not self.available(source, target):
            raise RuntimeError(
                f"No local Argos translation is available for {source}->{target}."
            )
        else:
            try:
                translated = self._translate.translate(segment.text, source, target)
            except Exception as exc:
                raise RuntimeError(
                    f"Local Argos translation failed for {source}->{target}."
                ) from exc

        return TranslationSegment(
            segment,
            translated,
            target,
            datetime.now(timezone.utc),
        )

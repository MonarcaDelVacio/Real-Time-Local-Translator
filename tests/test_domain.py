from datetime import datetime, timezone
from app.domain.models import DetectedLanguage, TranscriptSegment, TranslationSegment


def test_transcript_segment() -> None:
    segment = TranscriptSegment("hello", 0.0, 1.0, "en", 0.95)
    assert segment.text == "hello"
    assert segment.language_code == "en"


def test_translation_keeps_source() -> None:
    source = TranscriptSegment("hello", 0.0, 1.0, "en")
    result = TranslationSegment(source, "hola", "es", datetime.now(timezone.utc))
    assert result.source is source
    assert result.translated_text == "hola"


def test_unknown_language() -> None:
    result = DetectedLanguage(None, None, "unknown")
    assert result.code is None
    assert result.source == "unknown"

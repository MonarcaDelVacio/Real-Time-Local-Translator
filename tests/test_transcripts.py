from app.presentation.main_window import append_transcript_text


def test_transcript_saves_only_normalized_text_and_joins_fragments(tmp_path):
    path = tmp_path / "original.txt"

    append_transcript_text(path, "  Hello   there ")
    append_transcript_text(path, "how are   you?")

    assert path.read_text(encoding="utf-8") == "Hello there how are you?"


def test_transcript_starts_new_paragraph_after_sentence(tmp_path):
    path = tmp_path / "original.txt"

    append_transcript_text(path, "First sentence.")
    append_transcript_text(path, "Second sentence!")

    assert path.read_text(encoding="utf-8") == "First sentence.\n\nSecond sentence!"


def test_transcript_paragraph_separator_handles_utf8_ellipsis(tmp_path):
    path = tmp_path / "original.txt"

    append_transcript_text(path, "La frase terminó…")
    append_transcript_text(path, "Siguiente frase")

    assert path.read_text(encoding="utf-8") == "La frase terminó…\\n\\nSiguiente frase"

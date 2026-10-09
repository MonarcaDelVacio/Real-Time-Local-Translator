from app.presentation.main_window import append_conversation_entry


def test_conversation_history_appends_entries_without_overwriting(tmp_path):
    history = tmp_path / "Historial_traduccion.txt"
    append_conversation_entry(history, "  Hello   there. ", " Hola   a todos. ")
    first = history.read_text(encoding="utf-8")

    append_conversation_entry(history, "How are you?", "¿Cómo estás?")
    final = history.read_text(encoding="utf-8")

    assert "Original: Hello there." in final
    assert "Traducción: Hola a todos." in final
    assert "Original: How are you?" in final
    assert "Traducción: ¿Cómo estás?" in final
    assert final.startswith(first)
    assert final.count("Original:") == 2


def test_conversation_history_handles_empty_values(tmp_path):
    history = tmp_path / "Historial_traduccion.txt"
    append_conversation_entry(history, "  ", "  ")
    assert not history.exists()

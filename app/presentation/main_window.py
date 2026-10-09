from __future__ import annotations

import threading


def append_transcript_text(path, text: str) -> None:
    """Append normalized recognized text without fragile text-mode seeks."""
    from pathlib import Path

    clean_text = " ".join(text.split())
    if not clean_text:
        return

    target = Path(path)
    separator = ""
    if target.is_file() and target.stat().st_size:
        # TextIOWrapper.tell() returns an opaque seek cookie, not a byte/character
        # offset. Read a few bytes from the end instead; sentence punctuation is
        # ASCII except for the UTF-8 ellipsis.
        size = target.stat().st_size
        with target.open("rb") as transcript_file:
            transcript_file.seek(max(0, size - 3))
            tail = transcript_file.read()
        if tail.endswith((b".", b"!", b"?", "…".encode("utf-8"))):
            separator = "\n\n"
        else:
            separator = " "

    with target.open("a", encoding="utf-8") as transcript_file:
        transcript_file.write(separator + clean_text)


def append_conversation_entry(path, source: str, translated: str) -> None:
    """Persist one finalized source/translation pair without rewriting prior history."""
    from datetime import datetime
    from pathlib import Path

    original = " ".join(source.split())
    result = " ".join(translated.split())
    if not original and not result:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with target.open("a", encoding="utf-8") as history_file:
        history_file.write(f"[{timestamp}]\n")
        if original:
            history_file.write(f"Original: {original}\n")
        if result:
            history_file.write(f"Traducción: {result}\n")
        history_file.write("\n")


def run_gui(application) -> int:
    import os
    from pathlib import Path
    from datetime import datetime
    from PySide6.QtCore import QThread, Signal, QSettings, Qt, QUrl
    from PySide6.QtGui import QPalette, QDesktopServices, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QDialog,
        QTextEdit,
        QDialogButtonBox,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )


    class ModelSetupWorker(QThread):
        status_changed = Signal(str)
        finished_ok = Signal()
        failed = Signal(str)

        def run(self):
            try:
                from app.infrastructure.model_manager import ensure_models
                ensure_models(self.status_changed.emit)
                self.finished_ok.emit()
            except Exception as exc:
                import traceback
                self.failed.emit(f"{exc}\n\n{traceback.format_exc()}")

    class Worker(QThread):
        translated = Signal(str, str, str, bool)
        transcript = Signal(str)
        status_changed = Signal(str)
        initialization_finished = Signal()
        failed = Signal(str)
        finished_cleanly = Signal()

        def __init__(self, app, target_language):
            super().__init__()
            self.app = app
            self.target_language = target_language
            self.stop_flag = threading.Event()
            self.error_message = None
            self.last_reported_error = None

        def _report_error(self, error):
            self.last_reported_error = str(error)
            self.failed.emit(self.last_reported_error)

        def run(self):
            try:
                self.status_changed.emit("Inicializando motores locales…")
                pipe = self.app.create_pipeline()
                self.initialization_finished.emit()
                pipe.target_language = self.target_language
                self.status_changed.emit("Capturando audio — ASR streaming…")
                pipe.run(
                    lambda x: self.translated.emit(
                        x.source.language_code or "auto",
                        x.translated_text,
                        x.source.text,
                        x.source.is_final,
                    ),
                    self.stop_flag.is_set,
                    self._report_error,
                    lambda segment: self.transcript.emit(segment.text),
                )
            except Exception as exc:
                import traceback
                self.error_message = f"{exc}\n\n{traceback.format_exc()}"
                self.failed.emit(str(exc))
            finally:
                self.finished_cleanly.emit()

        def stop(self):
            self.stop_flag.set()

    app = QApplication.instance() or QApplication([])
    settings = QSettings("MonarcaDelVacio", "RealTimeLocalTranslator")

    # Resolve "Sistema" against the native palette before applying our own stylesheet.
    system_palette_dark = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
    current_theme = {"dark": True}

    def stylesheet_for(dark):
        if dark:
            return """
                QWidget { font-size: 13px; }
                QMainWindow, QDialog { background: #111827; }
                QLabel { color: #dbe4f0; }
                QFrame#header, QFrame#toolbar, QFrame#statusbar {
                    background: #182235; border: 1px solid #26344a; border-radius: 10px;
                }
                QLabel#appTitle { font-size: 24px; font-weight: 700; color: #f8fafc; }
                QLabel#subtitle { color: #94a3b8; }
                QLabel#status { color: #93c5fd; font-weight: 600; }
                QComboBox, QSpinBox, QPushButton {
                    background: #202c40; color: #e5edf7; border: 1px solid #35445b;
                    border-radius: 7px; padding: 7px 10px; min-height: 18px;
                }
                QComboBox:hover, QSpinBox:hover, QPushButton:hover { border-color: #60a5fa; }
                QPushButton { font-weight: 600; }
                QPushButton#primary { background: #2563eb; border-color: #3b82f6; }
                QPushButton#primary:hover { background: #1d4ed8; }
                QPushButton#danger { background: #3b2430; }
                QCheckBox { color: #cbd5e1; spacing: 7px; }
                QPlainTextEdit, QTextEdit {
                    background: #0b1220; color: #e5edf7; border: 1px solid #26344a;
                    border-radius: 10px; padding: 12px; selection-background-color: #2563eb;
                }
                QProgressBar {
                    background: #202c40; border: 1px solid #35445b; border-radius: 7px;
                    text-align: center; color: #e5edf7; min-height: 22px;
                }
                QProgressBar::chunk { background: #2563eb; border-radius: 6px; }
            """
        return """
            QWidget { font-size: 13px; }
            QMainWindow, QDialog { background: #f3f6fb; }
            QLabel { color: #1e293b; }
            QFrame#header, QFrame#toolbar, QFrame#statusbar {
                background: #ffffff; border: 1px solid #d5deea; border-radius: 10px;
            }
            QLabel#appTitle { font-size: 24px; font-weight: 700; color: #0f172a; }
            QLabel#subtitle { color: #64748b; }
            QLabel#status { color: #1d4ed8; font-weight: 600; }
            QComboBox, QSpinBox, QPushButton {
                background: #ffffff; color: #1e293b; border: 1px solid #cbd5e1;
                border-radius: 7px; padding: 7px 10px; min-height: 18px;
            }
            QComboBox:hover, QSpinBox:hover, QPushButton:hover { border-color: #3b82f6; }
            QPushButton { font-weight: 600; }
            QPushButton#primary { background: #2563eb; color: #ffffff; border-color: #3b82f6; }
            QPushButton#primary:hover { background: #1d4ed8; }
            QPushButton#danger { background: #fee2e2; color: #991b1b; }
            QCheckBox { color: #334155; spacing: 7px; }
            QPlainTextEdit, QTextEdit {
                background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 10px; padding: 12px; selection-background-color: #bfdbfe;
            }
            QProgressBar {
                background: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 7px;
                text-align: center; color: #1e293b; min-height: 22px;
            }
            QProgressBar::chunk { background: #2563eb; border-radius: 6px; }
        """

    def apply_theme(theme_name):
        dark = system_palette_dark if theme_name == "Sistema" else theme_name == "Oscuro"
        current_theme["dark"] = dark
        app.setStyleSheet(stylesheet_for(dark))
        for key in ("output", "original_output"):
            if key in globals_for_theme and "font_size" in globals_for_theme:
                globals_for_theme[key].setStyleSheet(
                    f"background-color: {'#0b1220' if dark else '#ffffff'}; "
                    f"color: {'#e5edf7' if dark else '#0f172a'}; "
                    f"font-size: {globals_for_theme['font_size'].value()}px; "
                    f"border: 1px solid {'#26344a' if dark else '#cbd5e1'}; "
                    "border-radius: 10px; padding: 12px; selection-background-color: #2563eb;"
                )
        for key in ("live_translation", "live_original"):
            if key in globals_for_theme:
                globals_for_theme[key].setStyleSheet(
                    "QLabel { "
                    f"background: {'#17243a' if dark else '#dbeafe'}; "
                    f"color: {'#bfdbfe' if dark else '#1e40af'}; "
                    f"border: 1px solid {'#2b4264' if dark else '#93c5fd'}; "
                    "border-radius: 8px; padding: 10px 12px; "
                    f"font-size: {globals_for_theme['font_size'].value() if 'font_size' in globals_for_theme else 14}px; "
                    "font-weight: 600; }"
                )

    globals_for_theme = {}
    apply_theme(str(settings.value("theme", "Oscuro")))

    class MainWindow(QMainWindow):
        def closeEvent(self, event):
            handler = getattr(self, "_close_event_handler", None)
            if handler is not None:
                handler(event)
                if not event.isAccepted():
                    return
            super().closeEvent(event)

    window = MainWindow()
    window.setWindowTitle("Real-Time Local Translator — Experimental 0.4.2")
    window.resize(1080, 720)
    window.setMinimumSize(820, 560)

    # Restore the user's experience preferences between launches.
    saved_geometry = settings.value("window/geometry")
    if saved_geometry:
        window.restoreGeometry(saved_geometry)
    always_on_top = settings.value("window/always_on_top", True, type=bool)
    if always_on_top:
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)

    header = QFrame()
    header.setObjectName("header")
    header_layout = QVBoxLayout(header)
    header_layout.setContentsMargins(18, 14, 18, 14)
    title = QLabel("Real-Time Local Translator")
    title.setObjectName("appTitle")
    subtitle = QLabel("Traducción de voz en tiempo real · procesamiento local · Inglés ↔ Español")
    subtitle.setObjectName("subtitle")
    header_layout.addWidget(title)
    header_layout.addWidget(subtitle)

    statusbar = QFrame()
    statusbar.setObjectName("statusbar")
    status_layout = QHBoxLayout(statusbar)
    status_layout.setContentsMargins(12, 8, 12, 8)
    status = QLabel("●  Listo · procesamiento local")
    status.setObjectName("status")
    status_layout.addWidget(status)
    status_layout.addStretch()

    toolbar = QFrame()
    toolbar.setObjectName("toolbar")
    row = QHBoxLayout(toolbar)
    row.setContentsMargins(12, 9, 12, 9)
    row.setSpacing(9)

    row.addStretch()

    start = QPushButton("▶  Iniciar")
    start.setObjectName("primary")
    stop = QPushButton("■  Detener")
    stop.setObjectName("danger")
    clear = QPushButton("Limpiar")
    settings_button = QPushButton("⚙  Ajustes")
    start.setToolTip("Comenzar la captura y traducción del audio del sistema")
    stop.setToolTip("Detener la captura")
    clear.setToolTip("Borrar solo el historial visible; los archivos guardados no se eliminan")
    settings_button.setToolTip("Configurar idioma, apariencia y opciones de visualización")
    row.addWidget(start)
    row.addWidget(stop)
    row.addWidget(clear)
    row.addWidget(settings_button)

    initialization = QProgressBar()
    initialization.setRange(0, 0)
    initialization.setTextVisible(True)
    initialization.setFormat("Inicializando motores locales…")
    initialization.setVisible(False)
    initialization.setMinimumHeight(22)

    live_row = QHBoxLayout()
    live_original = QLabel("Original en vivo: esperando audio…")
    live_original.setWordWrap(True)
    live_original.setMinimumHeight(52)
    live_translation = QLabel("Traducción en vivo: esperando audio…")
    live_translation.setWordWrap(True)
    live_translation.setMinimumHeight(52)
    live_row.addWidget(live_original, 1)
    live_row.addWidget(live_translation, 1)

    original_panel = QWidget()
    original_column = QVBoxLayout(original_panel)
    original_column.setContentsMargins(0, 0, 0, 0)
    original_column.setSpacing(6)
    original_heading = QLabel("TEXTO ORIGINAL")
    original_heading.setStyleSheet("font-weight: 700;")
    original_output = QTextEdit()
    original_output.setReadOnly(True)
    original_output.setAcceptRichText(True)
    original_output.setPlaceholderText("La transcripción reconocida aparecerá aquí, sin mezclarse con la traducción.")
    original_column.addWidget(original_heading)
    original_column.addWidget(original_output, 1)

    translated_panel = QWidget()
    translated_column = QVBoxLayout(translated_panel)
    translated_column.setContentsMargins(0, 0, 0, 0)
    translated_column.setSpacing(6)
    translated_heading = QLabel("TEXTO TRADUCIDO")
    translated_heading.setStyleSheet("font-weight: 700;")
    output = QTextEdit()
    output.setReadOnly(True)
    output.setAcceptRichText(True)
    output.setPlaceholderText(
        "Cuando estés listo, pulsa «Iniciar» y reproduce una voz por los altavoces o auriculares de Windows.\n\n"
        "Las traducciones confirmadas aparecerán aquí y se acumularán."
    )
    translated_column.addWidget(translated_heading)
    translated_column.addWidget(output, 1)

    history_row = QHBoxLayout()
    history_row.setSpacing(12)
    history_row.addWidget(original_panel, 1)
    history_row.addWidget(translated_panel, 1)
    original_panel.setVisible(show_original.isChecked())

    globals_for_theme["output"] = output
    globals_for_theme["original_output"] = original_output
    globals_for_theme["live_original"] = live_original
    globals_for_theme["live_translation"] = live_translation

    layout.addWidget(header)
    layout.addWidget(statusbar)
    layout.addWidget(initialization)
    layout.addWidget(toolbar)
    layout.addLayout(live_row)
    layout.addLayout(history_row, 1)
    window.setCentralWidget(central)

    # Keep advanced controls together in a dedicated settings dialog.
    settings_dialog = QDialog(window)
    settings_dialog.setWindowTitle("Ajustes")
    settings_dialog.setModal(False)
    settings_dialog.resize(470, 390)
    settings_layout = QVBoxLayout(settings_dialog)
    settings_layout.setContentsMargins(22, 20, 22, 20)
    settings_layout.setSpacing(14)

    target_label = QLabel("Idioma de destino")
    target = QComboBox()
    target.addItem("🇪🇸  Español", "es")
    target.addItem("🇬🇧  English", "en")
    target.setCurrentIndex(0 if settings.value("target", "es") == "es" else 1)
    target.setToolTip("Idioma al que se traducirá el audio")
    settings_layout.addWidget(target_label)
    settings_layout.addWidget(target)

    show_original = QCheckBox("Mostrar también la transcripción original")
    show_original.setChecked(settings.value("show_original", True, type=bool))
    show_original.setToolTip("Mostrar el texto reconocido antes de la traducción")
    settings_layout.addWidget(show_original)

    font_row = QHBoxLayout()
    font_row.addWidget(QLabel("Tamaño del texto"))
    font_size = QSpinBox()
    font_size.setRange(10, 32)
    font_size.setValue(settings.value("font_size", 14, type=int))
    font_size.setSuffix(" px")
    font_size.setToolTip("Tamaño de letra de la transcripción y traducción")
    font_row.addWidget(font_size)
    settings_layout.addLayout(font_row)

    always_on_top_box = QCheckBox("Mantener la ventana siempre encima")
    always_on_top_box.setChecked(always_on_top)
    always_on_top_box.setToolTip("Mantener la ventana sobre las demás ventanas")
    settings_layout.addWidget(always_on_top_box)

    theme_row = QHBoxLayout()
    theme_row.addWidget(QLabel("Tema de la aplicación"))
    theme_combo = QComboBox()
    theme_combo.addItems(["Claro", "Oscuro", "Sistema"])
    saved_theme = str(settings.value("theme", "Oscuro"))
    theme_combo.setCurrentText(saved_theme if saved_theme in ("Claro", "Oscuro", "Sistema") else "Oscuro")
    theme_combo.setToolTip("Usar tema claro, oscuro o seguir el tema del sistema operativo")
    theme_row.addWidget(theme_combo, 1)
    settings_layout.addLayout(theme_row)

    globals_for_theme["font_size"] = font_size
    # Apply explicit QTextEdit colors after all theme controls have been created.
    apply_theme(theme_combo.currentText())

    open_transcripts = QPushButton("Abrir carpeta de transcripciones")
    open_transcripts.setToolTip("Abrir en el Explorador de Windows los archivos originales guardados")
    settings_layout.addWidget(open_transcripts)
    settings_layout.addStretch()

    settings_note = QLabel("Los cambios se guardan automáticamente.")
    settings_note.setWordWrap(True)
    settings_layout.addWidget(settings_note)

    worker = None
    transcript_path = None
    history_path = None

    def transcripts_directory():
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Real-Time Local Translator" / "transcripts"
        return Path.home() / "Documents" / "Real-Time Local Translator" / "Transcripciones"

    def open_transcripts_folder():
        folder = transcripts_directory()
        folder.mkdir(parents=True, exist_ok=True)
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        if not opened:
            QMessageBox.warning(window, "No se pudo abrir la carpeta", f"Abre esta ruta manualmente:\\n{folder}")

    def apply_selected_theme(name):
        apply_theme(name)
        settings.setValue("theme", name)
        settings_note.setText(f"Tema aplicado: {name}.")


    def show_error_dialog(title, message):
        # Use a real text editor instead of QMessageBox so the complete error can
        # be selected and copied with Ctrl+C, even when the system palette is odd.
        dialog = QDialog(window)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(760, 420)
        dialog.setStyleSheet("""
            QDialog { background: #111827; }
            QLabel { color: #e5edf7; }
            QTextEdit {
                background: #0b1220;
                color: #f8fafc;
                border: 1px solid #35445b;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #2563eb;
            }
            QPushButton {
                background: #202c40;
                color: #f8fafc;
                border: 1px solid #35445b;
                border-radius: 7px;
                padding: 7px 14px;
            }
            QPushButton:hover { border-color: #60a5fa; }
        """)
        dialog_layout = QVBoxLayout(dialog)
        label = QLabel("La aplicación no pudo iniciar los motores locales. El texto de abajo se puede seleccionar y copiar con Ctrl+C:")
        label.setWordWrap(True)
        dialog_layout.addWidget(label)

        error_box = QTextEdit()
        error_box.setReadOnly(True)
        error_box.setPlainText(str(message))
        error_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        error_box.selectAll()
        dialog_layout.addWidget(error_box, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy_button = QPushButton("Copiar error")
        buttons.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(error_box.toPlainText()))
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        dialog.exec()

    def save_preferences():
        settings.setValue("window/geometry", window.saveGeometry())
        settings.setValue("window/always_on_top", always_on_top_box.isChecked())
        settings.setValue("target", target.currentData())
        settings.setValue("show_original", show_original.isChecked())
        settings.setValue("font_size", font_size.value())
        settings.setValue("theme", theme_combo.currentText())

    def set_always_on_top(enabled):
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        settings.setValue("window/always_on_top", enabled)
        window.show()

    def finish_session():
        initialization.setVisible(False)
        start.setEnabled(True)
        stop.setEnabled(False)
        target.setEnabled(True)
        font_size.setEnabled(True)
        always_on_top_box.setEnabled(True)
        theme_combo.setEnabled(True)

    def start_session():
        nonlocal worker, transcript_path, history_path
        if worker is not None and worker.isRunning():
            return
        save_preferences()
        transcript_path = None
        history_path = None
        live_original.setText("Original en vivo: esperando audio…")
        live_translation.setText("Traducción en vivo: esperando audio…")
        worker = Worker(application, target.currentData())
        initialization.setVisible(True)
        initialization.setFormat("Inicializando motores locales…")
        status.setText("●  Inicializando motores locales…")
        worker.translated.connect(append_translation)
        worker.transcript.connect(append_original_transcript)
        worker.status_changed.connect(lambda value: status.setText("●  " + value))
        worker.initialization_finished.connect(lambda: initialization.setVisible(False))
        worker.failed.connect(lambda error: status.setText(f"●  Error: {error}"))
        def handle_worker_finished():
            finish_session()
            if worker is not None and worker.error_message:
                status.setText(f"●  Error: {worker.error_message.splitlines()[0]}")
                show_error_dialog("No se pudo iniciar o continuar", worker.error_message)
            elif worker is not None and worker.last_reported_error:
                status.setText(f"●  Error durante la captura: {worker.last_reported_error}")
            else:
                status.setText("●  Detenido")

        worker.finished_cleanly.connect(handle_worker_finished)
        worker.start()
        start.setEnabled(False)
        stop.setEnabled(True)
        target.setEnabled(False)
        # Keep font-size adjustable while translation is running.
        always_on_top_box.setEnabled(False)
        theme_combo.setEnabled(False)

    def scroll_output_to_bottom(widget):
        scrollbar = widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def append_original_transcript(source):
        nonlocal transcript_path
        if not source or not source.strip():
            return
        try:
            folder = transcripts_directory()
            folder.mkdir(parents=True, exist_ok=True)
            if transcript_path is None:
                transcript_path = folder / f"Transcripcion_original_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.txt"
                transcript_path.write_text("", encoding="utf-8")
            append_transcript_text(transcript_path, source)
        except OSError as exc:
            status.setText(f"●  No se pudo guardar la transcripción: {exc}")

    def append_translation(lang, translated, source, is_final):
        nonlocal history_path
        from html import escape

        source_text = " ".join((source or "").split())
        translated_text = " ".join((translated or "").split())
        if not is_final:
            # Mutable hypotheses are shown in separate live panels; they never
            # enter the permanent transcript or overwrite finalized entries.
            if show_original.isChecked() and source_text:
                live_original.setText(f"Original en vivo: {source_text}")
            if translated_text:
                live_translation.setText(f"Traducción en vivo: {translated_text}")
            status.setText("●  Reconociendo y traduciendo; el historial confirmado se conserva…")
            return

        source_color = "#aebbc9" if current_theme["dark"] else "#64748b"
        translated_color = "#f8fafc" if current_theme["dark"] else "#0f172a"
        border_color = "#26344a" if current_theme["dark"] else "#d5deea"

        def append_entry(widget, html):
            scrollbar = widget.verticalScrollBar()
            follow_new_text = scrollbar.value() >= scrollbar.maximum() - 4
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml(html)
            cursor.insertBlock()
            widget.setTextCursor(cursor)
            if follow_new_text:
                scroll_output_to_bottom(widget)

        if source_text:
            append_entry(
                original_output,
                f'<div style="margin-bottom:12px; padding-bottom:10px; '
                f'border-bottom:1px solid {border_color}; color:{source_color};">'
                f'{escape(source_text)}</div>',
            )

        if translated_text:
            append_entry(
                output,
                f'<div style="margin-bottom:12px; padding-bottom:10px; '
                f'border-bottom:1px solid {border_color}; font-weight:700; color:{translated_color};">'
                f'{escape(translated_text)}</div>',
            )

        try:
            folder = transcripts_directory()
            folder.mkdir(parents=True, exist_ok=True)
            if history_path is None:
                history_path = folder / f"Historial_traduccion_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.txt"
                history_path.write_text("", encoding="utf-8")
            append_conversation_entry(history_path, source_text, translated_text)
        except OSError as exc:
            status.setText(f"●  No se pudo guardar el historial de traducción: {exc}")

        live_original.setText("Original en vivo: esperando el siguiente fragmento…")
        live_translation.setText("Traducción en vivo: esperando el siguiente fragmento…")
        status.setText("●  Fragmento confirmado; historial guardado")

    def stop_session():
        if worker is not None and worker.isRunning():
            # Do not block the GUI thread while audio/ASR cleanup completes.
            # Worker.finished_cleanly will restore controls when the thread exits.
            worker.stop()
            status.setText("●  Deteniendo captura y finalizando el texto pendiente…")
            stop.setEnabled(False)
            return
        finish_session()

    def clear_output():
        # This clears only the on-screen view. Saved transcript files remain intact.
        output.clear()
        original_output.clear()

    def change_font_size(value):
        settings.setValue("font_size", value)
        apply_theme(theme_combo.currentText())

    def close_event(event):
        save_preferences()
        # The first-run model worker may still be downloading/extracting large
        # files. Destroying its QThread wrapper while it runs can crash Qt.
        # Keep the window alive until preparation finishes; the user can still
        # switch to other applications because the setup dialog is non-modal.
        if setup_worker is not None and setup_worker.isRunning():
            QMessageBox.warning(
                window,
                "Preparación en curso",
                "La descarga o reparación de modelos todavía está en curso. "
                "Espera a que termine antes de cerrar la aplicación.",
            )
            event.ignore()
            return
        if worker is not None and worker.isRunning():
            worker.stop()
            if not worker.wait(5000):
                QMessageBox.warning(window, "Cierre pendiente", "La captura todavía está finalizando. Cierra la ventana cuando termine.")
                event.ignore()
                return
        event.accept()

    always_on_top_box.toggled.connect(set_always_on_top)
    font_size.valueChanged.connect(change_font_size)
    show_original.toggled.connect(lambda _: (original_panel.setVisible(show_original.isChecked()), save_preferences()))
    target.currentIndexChanged.connect(lambda _: save_preferences())
    theme_combo.currentTextChanged.connect(apply_selected_theme)
    open_transcripts.clicked.connect(open_transcripts_folder)
    settings_button.clicked.connect(settings_dialog.show)
    window._close_event_handler = close_event
    start.clicked.connect(start_session)
    stop.clicked.connect(stop_session)
    clear.clicked.connect(clear_output)
    stop.setEnabled(False)

    window.show()

    # Check the external model set before enabling a session. A dedicated, always-on-top
    # window appears only when something must be downloaded or repaired.
    from app.infrastructure.model_manager import models_ready
    setup_worker = None
    if not models_ready():
        start.setEnabled(False)
        status.setText("●  Preparando modelos y dependencias locales…")

        setup_dialog = QDialog(window)
        setup_dialog.setWindowTitle("Preparación inicial")
        # Preparation may download hundreds of megabytes. Keep this progress
        # window non-modal and not topmost so users can work in other applications.
        setup_dialog.setWindowModality(Qt.WindowModality.NonModal)
        setup_dialog.setMinimumWidth(520)
        setup_dialog.resize(560, 270)
        setup_dialog.setStyleSheet("""
            QDialog { background: #111827; }
            QLabel { color: #e5edf7; }
            QLabel#setupTitle { color: #f8fafc; font-size: 19px; font-weight: 700; }
            QLabel#setupNote { color: #94a3b8; }
            QPushButton {
                background: #2563eb; color: #ffffff; border: 1px solid #3b82f6;
                border-radius: 7px; padding: 8px 18px; font-weight: 600;
            }
        """)
        setup_layout = QVBoxLayout(setup_dialog)
        setup_layout.setContentsMargins(24, 22, 24, 22)
        setup_layout.setSpacing(12)

        setup_title = QLabel("Preparando Real-Time Local Translator")
        setup_title.setObjectName("setupTitle")
        setup_layout.addWidget(setup_title)

        setup_intro = QLabel(
            "Faltan modelos o dependencias necesarios. Se descargarán y verificarán "
            "antes de habilitar el botón «Iniciar»."
        )
        setup_intro.setWordWrap(True)
        setup_layout.addWidget(setup_intro)

        setup_stage = QLabel("Comprobando archivos locales…")
        setup_stage.setObjectName("status")
        setup_stage.setWordWrap(True)
        setup_layout.addWidget(setup_stage)

        setup_progress = QProgressBar()
        setup_progress.setRange(0, 0)
        setup_progress.setTextVisible(False)
        setup_progress.setMinimumHeight(18)
        setup_layout.addWidget(setup_progress)

        setup_note = QLabel(
            "Esta preparación normalmente solo se realiza la primera vez. "
            "Se repetirá únicamente si después faltan archivos o se detectan incompletos."
        )
        setup_note.setObjectName("setupNote")
        setup_note.setWordWrap(True)
        setup_layout.addWidget(setup_note)

        setup_button = QPushButton("Continuar")
        setup_button.setVisible(False)
        setup_layout.addWidget(setup_button, 0, Qt.AlignmentFlag.AlignRight)

        setup_failed_state = {"value": False}
        window._setup_dialog = setup_dialog

        def setup_finished():
            setup_failed_state["value"] = False
            setup_progress.setVisible(True)
            setup_progress.setRange(0, 100)
            setup_progress.setValue(100)
            setup_stage.setText("¡Todo listo! La aplicación ya está preparada para usarse.")
            setup_note.setText("Los modelos y las dependencias están instalados localmente. Pulsa «Continuar» y luego «Iniciar».")
            setup_button.setText("Continuar")
            setup_button.setVisible(True)
            start.setEnabled(True)
            status.setText("●  Listo · modelos verificados")

        def setup_failed(error):
            setup_failed_state["value"] = True
            setup_progress.setVisible(False)
            setup_stage.setText("No se pudo completar la preparación.")
            setup_note.setText("Comprueba la conexión y vuelve a intentarlo. También puedes copiar el error para compartirlo.")
            setup_button.setText("Reintentar")
            setup_button.setVisible(True)
            status.setText("●  Error al preparar modelos")
            show_error_dialog("No se pudieron preparar los modelos", error)

        def start_setup_worker():
            nonlocal setup_worker
            setup_worker = ModelSetupWorker()
            window._setup_worker = setup_worker
            setup_worker.status_changed.connect(
                lambda value: (setup_stage.setText(value), status.setText("●  " + value))
            )
            setup_worker.finished_ok.connect(setup_finished)
            setup_worker.failed.connect(setup_failed)
            setup_worker.start()

        def setup_action():
            if not setup_failed_state["value"]:
                setup_dialog.accept()
                return
            setup_failed_state["value"] = False
            setup_button.setVisible(False)
            setup_progress.setVisible(True)
            setup_progress.setRange(0, 0)
            setup_note.setText("Volviendo a comprobar y reparar los modelos locales…")
            setup_stage.setText("Reintentando la preparación…")
            status.setText("●  Reintentando preparación de modelos…")
            start_setup_worker()

        setup_button.clicked.connect(setup_action)
        def restore_window_topmost(_result):
            # Setup temporarily releases the main window's topmost flag. Restore
            # the current preference only after the progress dialog has closed.
            desired = always_on_top_box.isChecked()
            window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, desired)
            window.show()

        setup_dialog.finished.connect(restore_window_topmost)

        # The main window normally honors the user's always-on-top preference.
        # Temporarily release that flag during setup so other apps can be brought forward.
        if always_on_top:
            window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            window.show()
        setup_dialog.show()
        start_setup_worker()

    return app.exec()

from __future__ import annotations

import threading


def append_transcript_text(path, text: str) -> None:
    """Append only recognized words, formatting sentence boundaries for reading."""
    clean_text = " ".join(text.split())
    if not clean_text:
        return

    with open(path, "a+", encoding="utf-8") as transcript_file:
        transcript_file.seek(0, 2)
        file_size = transcript_file.tell()
        separator = ""
        if file_size:
            transcript_file.seek(file_size - 1)
            last_char = transcript_file.read(1)
            separator = "\n\n" if last_char in ".!?…" else " "
        transcript_file.seek(0, 2)
        transcript_file.write(separator + clean_text)


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
                self.failed.emit(str(exc))

    class Worker(QThread):
        translated = Signal(str, str, str, bool)
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
                )
            except Exception as exc:
                self.error_message = str(exc)
                self.failed.emit(self.error_message)
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
        if "output" in globals_for_theme:
            globals_for_theme["output"].setStyleSheet(
                f"background-color: {'#0b1220' if dark else '#ffffff'}; "
                f"color: {'#e5edf7' if dark else '#0f172a'}; "
                f"font-size: {globals_for_theme['font_size'].value()}px; "
                f"border: 1px solid {'#26344a' if dark else '#cbd5e1'}; "
                "border-radius: 10px; padding: 12px; selection-background-color: #2563eb;"
            )
        if "live_preview" in globals_for_theme:
            globals_for_theme["live_preview"].setStyleSheet(
                "QLabel { "
                f"background: {'#17243a' if dark else '#dbeafe'}; "
                f"color: {'#bfdbfe' if dark else '#1e40af'}; "
                f"border: 1px solid {'#2b4264' if dark else '#93c5fd'}; "
                "border-radius: 8px; padding: 10px 12px; "
                f"font-size: {globals_for_theme['font_size'].value()}px; font-weight: 600; }}"
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
    clear.setToolTip("Borrar el historial visible")
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

    live_preview = QLabel("")
    live_preview.setWordWrap(True)
    live_preview.setVisible(False)
    live_preview.setStyleSheet(
        "QLabel { background: #17243a; color: #bfdbfe; border: 1px solid #2b4264; "
        "border-radius: 8px; padding: 10px 12px; font-weight: 600; }"
    )

    output = QTextEdit()
    output.setReadOnly(True)
    output.setAcceptRichText(True)
    output.setPlaceholderText(
        "Cuando estés listo, pulsa «Iniciar» y reproduce una voz por los altavoces o auriculares de Windows.\n\n"
        "Las traducciones finales aparecerán aquí automáticamente."
    )
    globals_for_theme["output"] = output

    layout.addWidget(header)
    layout.addWidget(statusbar)
    layout.addWidget(initialization)
    layout.addWidget(toolbar)
    layout.addWidget(output, 1)
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
    # Track the temporary live entry inside the document so revisions replace it
    # in place without rebuilding the entire history on every update.
    provisional_start = None
    provisional_end = None

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
        nonlocal worker, transcript_path
        if worker is not None and worker.isRunning():
            return
        save_preferences()
        transcript_path = None
        worker = Worker(application, target.currentData())
        initialization.setVisible(True)
        initialization.setFormat("Inicializando motores locales…")
        status.setText("●  Inicializando motores locales…")
        worker.translated.connect(append_translation)
        worker.status_changed.connect(lambda value: status.setText("●  " + value))
        worker.initialization_finished.connect(lambda: initialization.setVisible(False))
        worker.failed.connect(lambda error: status.setText(f"●  Error: {error}"))
        def handle_worker_finished():
            finish_session()
            if worker is not None and worker.error_message:
                status.setText(f"●  Error: {worker.error_message}")
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

    def scroll_output_to_bottom():
        # Follow the newest text automatically, even during a long session.
        scrollbar = output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def append_translation(lang, translated, source, is_final):
        nonlocal transcript_path, provisional_start, provisional_end
        from html import escape

        source_color = "#aebbc9" if current_theme["dark"] else "#64748b"
        translated_color = "#f8fafc" if current_theme["dark"] else "#0f172a"
        source_html = (
            f'<div style="color:{source_color};">{escape(source)}</div>'
            if show_original.isChecked() and source and source.strip()
            else ""
        )
        if not is_final:
            # Update one provisional entry in place as the ASR revises its hypothesis.
            live_entry = (
                f'<div style="margin-bottom:14px; padding:8px; '
                f'border-left:3px solid #3b82f6;">'
                f'{source_html}'
                f'<div style="margin-top:4px; font-weight:700; color:{translated_color};">'
                f'{escape(translated)}</div>'
                f'<div style="margin-top:3px; color:{source_color}; font-size:11px;">En vivo · provisional</div>'
                f'</div>'
            )
            cursor = output.textCursor()
            if provisional_start is None or provisional_end is None:
                cursor.movePosition(QTextCursor.MoveOperation.End)
                provisional_start = cursor.position()
            else:
                cursor.setPosition(provisional_start)
                cursor.setPosition(provisional_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertHtml(live_entry)
            provisional_end = cursor.position()
            output.setTextCursor(cursor)
            scroll_output_to_bottom()
            status.setText("●  Transcribiendo y traduciendo en vivo…")
            return

        # Remove the temporary live entry before inserting the finalized phrase.
        if provisional_start is not None and provisional_end is not None:
            cursor = output.textCursor()
            cursor.setPosition(provisional_start)
            cursor.setPosition(provisional_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            output.setTextCursor(cursor)
            provisional_start = None
            provisional_end = None

        # Persist only finalized original-language text, independently of whether
        # the user chooses to display the original text in the UI.
        if source and source.strip():
            try:
                folder = transcripts_directory()
                folder.mkdir(parents=True, exist_ok=True)
                if transcript_path is None:
                    transcript_path = folder / f"Transcripcion_original_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.txt"
                    transcript_path.write_text("", encoding="utf-8")
                # Store plain recognized text only, without labels or timestamps.
                append_transcript_text(transcript_path, source)
            except OSError as exc:
                # A disk/permission problem must not discard the translation or
                # crash the GUI slot; surface the save failure instead.
                status.setText(f"●  No se pudo guardar la transcripción: {exc}")

        if show_original.isChecked():
            entry = (
                f'<div style="margin-bottom:14px;">'
                f'<div style="color:{source_color};">{escape(source)}</div>'
                f'<div style="margin-top:4px; font-weight:700; color:{translated_color};">'
                f'{escape(translated)}</div></div>'
            )
        else:
            entry = (
                f'<div style="margin-bottom:14px; font-weight:700; color:{translated_color};">'
                f'{escape(translated)}</div>'
            )
        cursor = output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(entry)
        output.setTextCursor(cursor)
        scroll_output_to_bottom()

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
        nonlocal provisional_start, provisional_end
        output.clear()
        provisional_start = None
        provisional_end = None

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
    show_original.toggled.connect(lambda _: save_preferences())
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
        setup_button.clicked.connect(setup_dialog.accept)
        setup_layout.addWidget(setup_button, 0, Qt.AlignmentFlag.AlignRight)

        setup_worker = ModelSetupWorker()
        window._setup_worker = setup_worker
        window._setup_dialog = setup_dialog
        setup_worker.status_changed.connect(lambda value: (setup_stage.setText(value), status.setText("●  " + value)))
        def setup_finished():
            setup_progress.setRange(0, 100)
            setup_progress.setValue(100)
            setup_stage.setText("¡Todo listo! La aplicación ya está preparada para usarse.")
            setup_note.setText("Los modelos y las dependencias están instalados localmente. Pulsa «Continuar» y luego «Iniciar».")
            setup_button.setVisible(True)
            start.setEnabled(True)
            status.setText("●  Listo · modelos verificados")
        def setup_failed(error):
            setup_progress.setVisible(False)
            setup_stage.setText("No se pudo completar la preparación.")
            setup_note.setText("Corrige el problema y vuelve a abrir la aplicación. Puedes copiar el mensaje de error para compartirlo.")
            setup_button.setText("Cerrar")
            setup_button.setVisible(True)
            status.setText("●  Error al preparar modelos")
            show_error_dialog("No se pudieron preparar los modelos", error)
        setup_worker.finished_ok.connect(setup_finished)
        setup_worker.failed.connect(setup_failed)

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
        setup_worker.start()

    return app.exec()

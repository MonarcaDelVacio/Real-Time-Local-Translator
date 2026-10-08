from __future__ import annotations

import threading


def run_gui(application) -> int:
    from PySide6.QtCore import QThread, Signal, QSettings, Qt
    from PySide6.QtGui import QFont
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
                    lambda e: self.failed.emit(str(e)),
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

    # A compact dark theme keeps the application readable during calls and media playback.
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QMainWindow { background: #111827; }
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
        QPlainTextEdit {
            background: #0b1220; color: #e5edf7; border: 1px solid #26344a;
            border-radius: 10px; padding: 12px;
            selection-background-color: #2563eb;
        }
        QProgressBar {
            background: #202c40; border: 1px solid #35445b; border-radius: 7px;
            text-align: center; color: #e5edf7; min-height: 22px;
        }
        QProgressBar::chunk { background: #2563eb; border-radius: 6px; }
    """)

    window = QMainWindow()
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

    row.addWidget(QLabel("Destino"))
    target = QComboBox()
    target.addItem("🇪🇸  Español", "es")
    target.addItem("🇬🇧  English", "en")
    target.setCurrentIndex(0 if settings.value("target", "es") == "es" else 1)
    target.setToolTip("Idioma al que se traducirá el audio")
    row.addWidget(target)

    show_original = QCheckBox("Original")
    show_original.setChecked(settings.value("show_original", True, type=bool))
    show_original.setToolTip("Mostrar también el texto reconocido antes de la traducción")
    row.addWidget(show_original)

    row.addWidget(QLabel("Texto"))
    font_size = QSpinBox()
    font_size.setRange(10, 32)
    font_size.setValue(settings.value("font_size", 14, type=int))
    font_size.setSuffix(" px")
    font_size.setToolTip("Tamaño de letra de la transcripción y traducción")
    row.addWidget(font_size)

    always_on_top_box = QCheckBox("Siempre encima")
    always_on_top_box.setChecked(always_on_top)
    always_on_top_box.setToolTip("Mantener la ventana sobre las demás ventanas")
    row.addWidget(always_on_top_box)
    row.addStretch()

    start = QPushButton("▶  Iniciar")
    start.setObjectName("primary")
    stop = QPushButton("■  Detener")
    stop.setObjectName("danger")
    clear = QPushButton("Limpiar")
    start.setToolTip("Comenzar la captura y traducción del audio del sistema")
    stop.setToolTip("Detener la captura")
    clear.setToolTip("Borrar el historial visible")
    row.addWidget(start)
    row.addWidget(stop)
    row.addWidget(clear)

    initialization = QProgressBar()
    initialization.setRange(0, 0)
    initialization.setTextVisible(True)
    initialization.setFormat("Inicializando motores locales…")
    initialization.setVisible(False)
    initialization.setMinimumHeight(22)

    output = QTextEdit()
    output.setReadOnly(True)
    output.setAcceptRichText(True)
    output.setPlaceholderText(
        "Cuando estés listo, pulsa «Iniciar» y reproduce una voz por los altavoces o auriculares de Windows.\n\n"
        "Las traducciones finales aparecerán aquí automáticamente."
    )
    output.setStyleSheet(f"font-size: {font_size.value()}px;")

    layout.addWidget(header)
    layout.addWidget(statusbar)
    layout.addWidget(initialization)
    layout.addWidget(toolbar)
    layout.addWidget(output, 1)
    window.setCentralWidget(central)

    worker = None

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

    def start_session():
        nonlocal worker
        if worker is not None and worker.isRunning():
            return
        save_preferences()
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
                show_error_dialog("No se pudo iniciar", worker.error_message)
            else:
                status.setText("●  Detenido")

        worker.finished_cleanly.connect(handle_worker_finished)
        worker.start()
        start.setEnabled(False)
        stop.setEnabled(True)
        target.setEnabled(False)
        font_size.setEnabled(False)
        always_on_top_box.setEnabled(False)

    def append_translation(lang, translated, source, is_final):
        if not is_final:
            status.setText(f"●  En vivo: {translated}")
            return

        from html import escape

        if show_original.isChecked():
            output.append(
                f'<div style="margin-bottom: 14px;">'
                f'<div style="color:#aebbc9;">{escape(source)}</div>'
                f'<div style="margin-top:4px; font-weight:700; color:#f8fafc;">{escape(translated)}</div>'
                f'</div>'
            )
        else:
            output.append(
                f'<div style="margin-bottom: 14px; font-weight:700; color:#f8fafc;">'
                f'{escape(translated)}</div>'
            )

    def stop_session():
        if worker is not None and worker.isRunning():
            worker.stop()
            status.setText("●  Deteniendo…")
            if not worker.wait(5000):
                QMessageBox.warning(window, "Cierre pendiente", "El motor todavía está finalizando la captura. Espera unos segundos.")
                return
        finish_session()

    def clear_output():
        output.clear()

    def change_font_size(value):
        output.setStyleSheet(f"font-size: {value}px;")
        settings.setValue("font_size", value)

    def close_event(event):
        save_preferences()
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
    window.closeEvent = close_event
    start.clicked.connect(start_session)
    stop.clicked.connect(stop_session)
    clear.clicked.connect(clear_output)
    stop.setEnabled(False)

    window.show()
    return app.exec()

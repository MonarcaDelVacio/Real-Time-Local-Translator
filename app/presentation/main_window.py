from __future__ import annotations

import threading


def run_gui(application) -> int:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
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
                self.failed.emit(str(exc))
            finally:
                self.finished_cleanly.emit()

        def stop(self):
            self.stop_flag.set()

    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.setWindowTitle("Real-Time Local Translator — Experimental 0.4.1")
    window.resize(1000, 700)

    central = QWidget()
    layout = QVBoxLayout(central)

    title = QLabel("Real-Time Local Translator")
    title.setStyleSheet("font-size: 22px; font-weight: 600;")
    status = QLabel("Listo — procesamiento local")

    target = QComboBox()
    target.addItem("Español", "es")
    target.addItem("English", "en")

    show_original = QCheckBox("Mostrar texto original")
    show_original.setChecked(True)

    font_size = QSpinBox()
    font_size.setRange(10, 32)
    font_size.setValue(14)
    font_size.setSuffix(" px")
    font_size.setToolTip("Tamaño de letra de la transcripción y traducción")

    output = QPlainTextEdit()
    output.setReadOnly(True)
    output.setPlaceholderText(
        "Reproduce una voz por los altavoces/auriculares de Windows y pulsa Iniciar…"
    )
    output.setStyleSheet(f"font-size: {font_size.value()}px;")

    initialization = QProgressBar()
    initialization.setRange(0, 0)
    initialization.setTextVisible(True)
    initialization.setFormat("Inicializando motores locales…")
    initialization.setVisible(False)
    initialization.setMinimumHeight(22)

    start = QPushButton("Iniciar")
    stop = QPushButton("Detener")
    clear = QPushButton("Limpiar")

    row = QHBoxLayout()
    row.addWidget(QLabel("Idioma destino:"))
    row.addWidget(target)
    row.addWidget(show_original)
    row.addWidget(QLabel("Tamaño:"))
    row.addWidget(font_size)
    row.addStretch()
    row.addWidget(start)
    row.addWidget(stop)
    row.addWidget(clear)

    layout.addWidget(title)
    layout.addWidget(
        QLabel("Experimental: ASR streaming estabilizado Inglés ↔ Español")
    )
    layout.addWidget(status)
    layout.addWidget(initialization)
    layout.addLayout(row)
    layout.addWidget(output)
    window.setCentralWidget(central)

    worker = None

    def finish_session():
        status.setText("Detenido")
        initialization.setVisible(False)
        start.setEnabled(True)
        stop.setEnabled(False)
        target.setEnabled(True)
        font_size.setEnabled(True)

    def start_session():
        nonlocal worker
        if worker is not None and worker.isRunning():
            return

        worker = Worker(application, target.currentData())

        initialization.setVisible(True)
        initialization.setFormat("Inicializando motores locales…")
        status.setText("Inicializando motores locales…")

        worker.translated.connect(append_translation)
        worker.status_changed.connect(status.setText)
        worker.initialization_finished.connect(
            lambda: initialization.setVisible(False)
        )
        worker.failed.connect(lambda error: status.setText(f"Error: {error}"))
        worker.finished_cleanly.connect(finish_session)
        worker.start()

        start.setEnabled(False)
        stop.setEnabled(True)
        target.setEnabled(False)
        font_size.setEnabled(False)

    def append_translation(lang, translated, source, is_final):
        target_code = target.currentData()
        if not is_final:
            status.setText(f"En vivo: {translated}")
            return

        if show_original.isChecked():
            output.appendPlainText(
                f"[{lang} → {target_code}]\n"
                f"Original: {source}\n"
                f"Traducción: {translated}\n"
            )
        else:
            output.appendPlainText(
                f"[{lang} → {target_code}]\n"
                f"{translated}\n"
            )

    def stop_session():
        if worker is not None and worker.isRunning():
            worker.stop()
            status.setText("Deteniendo…")
            if not worker.wait(5000):
                QMessageBox.warning(
                    window,
                    "Cierre pendiente",
                    "El motor todavía está finalizando la captura. Espera unos segundos.",
                )
                return
        finish_session()

    def clear_output():
        output.clear()

    def change_font_size(value):
        output.setStyleSheet(f"font-size: {value}px;")

    font_size.valueChanged.connect(change_font_size)

    def close_event(event):
        if worker is not None and worker.isRunning():
            worker.stop()
            if not worker.wait(5000):
                QMessageBox.warning(
                    window,
                    "Cierre pendiente",
                    "La captura todavía está finalizando. Cierra la ventana cuando termine.",
                )
                event.ignore()
                return
        event.accept()

    window.closeEvent = close_event
    start.clicked.connect(start_session)
    stop.clicked.connect(stop_session)
    clear.clicked.connect(clear_output)
    stop.setEnabled(False)

    window.show()
    return app.exec()

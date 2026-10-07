from __future__ import annotations

import threading


def run_gui(application) -> int:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    class Worker(QThread):
        translated = Signal(str, str, str)
        status_changed = Signal(str)
        failed = Signal(str)
        finished_cleanly = Signal()

        def __init__(self, app, target_language):
            super().__init__()
            self.app = app
            self.target_language = target_language
            self.stop_flag = threading.Event()

        def run(self):
            try:
                self.status_changed.emit("Cargando motores locales…")
                pipe = self.app.create_pipeline()
                pipe.target_language = self.target_language
                self.status_changed.emit("Capturando audio del sistema…")
                pipe.run(
                    lambda x: self.translated.emit(
                        x.source.language_code or "auto",
                        x.translated_text,
                        x.source.text,
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
    window.setWindowTitle("Real-Time Local Translator")
    window.resize(1000, 700)

    central = QWidget()
    layout = QVBoxLayout(central)

    title = QLabel("Real-Time Local Translator")
    title.setStyleSheet("font-size: 22px; font-weight: 600;")
    status = QLabel("Listo — procesamiento local")

    target = QComboBox()
    languages = [
        ("Español", "es"), ("English", "en"), ("Português", "pt"),
        ("Français", "fr"), ("Deutsch", "de"), ("Italiano", "it"),
        ("日本語", "ja"), ("한국어", "ko"), ("中文", "zh"),
    ]
    for name, code in languages:
        target.addItem(name, code)

    output = QPlainTextEdit()
    output.setReadOnly(True)
    output.setPlaceholderText("Las traducciones aparecerán aquí…")

    start = QPushButton("Iniciar")
    stop = QPushButton("Detener")
    clear = QPushButton("Limpiar")

    row = QHBoxLayout()
    row.addWidget(QLabel("Idioma destino:"))
    row.addWidget(target)
    row.addStretch()
    row.addWidget(start)
    row.addWidget(stop)
    row.addWidget(clear)

    layout.addWidget(title)
    layout.addWidget(status)
    layout.addLayout(row)
    layout.addWidget(output)
    window.setCentralWidget(central)

    worker = None

    def start_session():
        nonlocal worker
        if worker is not None and worker.isRunning():
            return

        worker = Worker(application, target.currentData())
        worker.translated.connect(
            lambda lang, translated, source: output.appendPlainText(
                f"[{lang} → {target.currentData()}]\n"
                f"{translated}\n"
            )
        )
        worker.status_changed.connect(status.setText)
        worker.failed.connect(lambda error: status.setText(f"Error: {error}"))
        worker.finished_cleanly.connect(lambda: status.setText("Detenido"))
        worker.start()

        start.setEnabled(False)
        stop.setEnabled(True)
        target.setEnabled(False)

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
        start.setEnabled(True)
        stop.setEnabled(False)
        target.setEnabled(True)

    def clear_output():
        output.clear()

    def close_event(event):
        if worker is not None and worker.isRunning():
            worker.stop()
            worker.wait(5000)
        event.accept()

    window.closeEvent = close_event
    start.clicked.connect(start_session)
    stop.clicked.connect(stop_session)
    clear.clicked.connect(clear_output)
    stop.setEnabled(False)

    window.show()
    return app.exec()

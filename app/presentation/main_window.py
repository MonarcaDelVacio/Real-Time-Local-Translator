from __future__ import annotations

import threading


def run_gui(pipeline=None) -> int:
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
        translated = Signal(str, str)
        failed = Signal(str)
        finished_cleanly = Signal()

        def __init__(self, pipe):
            super().__init__()
            self.pipe = pipe
            self.stop_flag = threading.Event()

        def run(self):
            try:
                if self.pipe is None:
                    raise RuntimeError(
                        "El motor local no está disponible. Ejecuta primero la preparación de modelos."
                    )
                self.pipe.run(
                    lambda x: self.translated.emit(
                        x.source.language_code or "auto", x.translated_text
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
    window.resize(980, 680)

    central = QWidget()
    layout = QVBoxLayout(central)
    title = QLabel("Real-Time Local Translator")
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
        if pipeline is None:
            QMessageBox.critical(
                window,
                "No disponible",
                "No se pudo construir el motor local. Ejecuta primero la preparación de modelos.",
            )
            return
        pipeline.target_language = target.currentData()
        worker = Worker(pipeline)
        worker.translated.connect(
            lambda lang, text: output.appendPlainText(
                f"[{lang} → {pipeline.target_language}] {text}"
            )
        )
        worker.failed.connect(lambda error: status.setText(f"Error: {error}"))
        worker.finished_cleanly.connect(lambda: status.setText("Detenido"))
        worker.start()
        status.setText("Capturando audio del sistema…")
        start.setEnabled(False)
        stop.setEnabled(True)

    def stop_session():
        if worker is not None and worker.isRunning():
            worker.stop()
            status.setText("Deteniendo…")
            worker.wait(3000)
        start.setEnabled(True)
        stop.setEnabled(False)

    def clear_output():
        output.clear()

    start.clicked.connect(start_session)
    stop.clicked.connect(stop_session)
    clear.clicked.connect(clear_output)
    stop.setEnabled(False)
    window.show()
    return app.exec()

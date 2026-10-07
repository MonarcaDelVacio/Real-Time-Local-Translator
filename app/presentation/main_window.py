from __future__ import annotations
import os
import threading
from pathlib import Path


def run_gui(pipeline=None) -> int:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget

    class Worker(QThread):
        translated = Signal(str)
        failed = Signal(str)
        def __init__(self, pipe): super().__init__(); self.pipe = pipe; self.stop_flag = threading.Event()
        def run(self):
            try:
                if self.pipe is None: raise RuntimeError("Audio/ASR pipeline is not configured yet.")
                self.pipe.run(lambda x: self.translated.emit(x.translated_text), self.stop_flag.is_set)
            except Exception as exc: self.failed.emit(str(exc))
        def stop(self): self.stop_flag.set()

    app = QApplication.instance() or QApplication([])
    window = QMainWindow(); window.setWindowTitle("Real-Time Local Translator"); window.resize(900, 600)
    central = QWidget(); layout = QVBoxLayout(central)
    status = QLabel("Listo — procesamiento local")
    target = QComboBox(); target.addItems(["es", "en", "pt", "fr", "de", "it", "ja", "ko", "zh"])
    output = QPlainTextEdit(); output.setReadOnly(True)
    start = QPushButton("Iniciar traducción"); stop = QPushButton("Detener")
    layout.addWidget(status); layout.addWidget(target); layout.addWidget(output); layout.addWidget(start); layout.addWidget(stop)
    window.setCentralWidget(central)
    worker = None
    def start_session():
        nonlocal worker
        if pipeline is None:
            status.setText("Configura los modelos locales y reinicia la aplicación.")
            return
        pipeline.target_language = target.currentText()
        worker = Worker(pipeline); worker.translated.connect(lambda t: output.appendPlainText(t)); worker.failed.connect(lambda e: status.setText("Error: "+e)); worker.start(); status.setText("Escuchando audio del sistema…")
    def stop_session():
        if worker: worker.stop(); worker.wait(3000); status.setText("Detenido")
    start.clicked.connect(start_session); stop.clicked.connect(stop_session)
    window.show(); return app.exec()

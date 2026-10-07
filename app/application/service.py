from __future__ import annotations
from app.application.pipeline import TranslationPipeline

class TranslatorApplication:
    def __init__(self, pipeline: TranslationPipeline | None = None) -> None:
        self.pipeline = pipeline

    def run(self) -> int:
        from app.presentation.main_window import run_gui
        return run_gui(self.pipeline)

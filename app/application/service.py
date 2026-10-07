from __future__ import annotations

from collections.abc import Callable

from app.application.pipeline import TranslationPipeline


class TranslatorApplication:
    """Application shell with lazy runtime construction.

    Heavy ML/audio dependencies are created only when the user starts a session,
    so the GUI can open immediately and errors can be shown in the UI.
    """

    def __init__(
        self,
        pipeline: TranslationPipeline | None = None,
        pipeline_factory: Callable[[], TranslationPipeline] | None = None,
    ) -> None:
        if pipeline is not None and pipeline_factory is not None:
            raise ValueError("Provide a pipeline or a pipeline factory, not both.")
        self.pipeline = pipeline
        self._pipeline_factory = pipeline_factory

    def create_pipeline(self) -> TranslationPipeline:
        if self.pipeline is None:
            if self._pipeline_factory is None:
                raise RuntimeError("No local pipeline factory is configured.")
            self.pipeline = self._pipeline_factory()
        return self.pipeline

    def run(self) -> int:
        from app.presentation.main_window import run_gui

        return run_gui(self)

"""Application entry point."""
from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path


def _self_test() -> int:
    """Smoke-test runtime imports in source and frozen builds without opening the GUI."""
    modules = (
        "app.application.bootstrap",
        "app.application.pipeline",
        "app.infrastructure.model_manager",
        "engines.audio.soundcard_backend",
        "engines.asr.sherpa_streaming_engine",
        "engines.asr.faster_whisper_refiner",
        "engines.translation.argos_engine",
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "numpy",
        "soundcard",
        "sherpa_onnx",
        "faster_whisper",
        "ctranslate2",
        "argostranslate",
        "huggingface_hub",
        "tqdm",
        "tqdm.auto",
    )
    try:
        for module_name in modules:
            importlib.import_module(module_name)
    except Exception:
        try:
            log_path = Path(sys.argv[0]).resolve().parent / "self-test-error.log"
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        return 1
    return 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return _self_test()

    from app.application.bootstrap import build_application

    return build_application().run()


if __name__ == "__main__":
    raise SystemExit(main())

"""Application entry point."""
from __future__ import annotations

import importlib
import sys


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
        "numpy",
        "soundcard",
        "sherpa_onnx",
        "faster_whisper",
        "ctranslate2",
        "argostranslate",
        "huggingface_hub",
        "tqdm",
    )
    for module_name in modules:
        importlib.import_module(module_name)
    return 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        try:
            return _self_test()
        except Exception:
            return 1

    from app.application.bootstrap import build_application

    return build_application().run()


if __name__ == "__main__":
    raise SystemExit(main())

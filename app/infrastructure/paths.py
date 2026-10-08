from __future__ import annotations

from pathlib import Path
import sys


def project_root() -> Path:
    """Return the application directory, or the repository root during development."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def models_root() -> Path:
    """Return the external model directory, with legacy bundled-model fallback."""
    external = project_root() / "models"
    if external.exists():
        return external

    # Builds before the external-model layout stored models under PyInstaller's
    # internal directory. Keep this fallback so an update can reuse existing
    # models without forcing the user to download them again.
    legacy = project_root() / "_internal" / "models"
    if legacy.exists():
        return legacy

    return external


def whisper_model_path(model_name: str) -> Path:
    return models_root() / "whisper" / model_name

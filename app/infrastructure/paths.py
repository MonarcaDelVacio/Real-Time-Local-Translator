from __future__ import annotations

from pathlib import Path
import os
import sys


def project_root() -> Path:
    """Return the application directory during development or installation."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def models_root() -> Path:
    """Return the writable runtime model directory.

    Installed builds keep downloaded models in LOCALAPPDATA so the application
    can repair/update them without requiring administrator privileges.
    Developer builds continue to use the repository's models directory.
    """
    override = os.environ.get("RTL_MODELS_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Real-Time Local Translator" / "models"
    external = project_root() / "models"
    if external.exists():
        return external
    legacy = project_root() / "_internal" / "models"
    if legacy.exists():
        return legacy
    return external


def whisper_model_path(model_name: str) -> Path:
    return models_root() / "whisper" / model_name


def bundled_models_root() -> Path | None:
    """Return read-only model assets bundled by PyInstaller, if present."""
    if not getattr(sys, "frozen", False):
        return None
    candidates = (
        Path(getattr(sys, "_MEIPASS", project_root())) / "models",
        project_root() / "models",
        project_root() / "_internal" / "models",
    )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir():
            return resolved
    return None

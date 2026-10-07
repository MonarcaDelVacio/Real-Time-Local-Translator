from __future__ import annotations

from pathlib import Path
import sys


def project_root() -> Path:
    """Return the directory containing bundled application assets."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def whisper_model_path(model_name: str) -> Path:
    return project_root() / "models" / "whisper" / model_name

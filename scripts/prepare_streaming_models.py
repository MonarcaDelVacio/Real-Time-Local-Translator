"""Compatibility entry point for preparing runtime models during development/builds.

All download, repair and validation logic lives in app.infrastructure.model_manager
so the player installer and developer tools cannot drift apart.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RTL_MODELS_DIR", str(ROOT / "models"))


def main() -> None:
    from app.infrastructure.model_manager import ensure_models

    ensure_models(lambda message: print(message, flush=True))
    print("Local streaming models are ready.")


if __name__ == "__main__":
    main()

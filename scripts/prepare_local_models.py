"""Prepare the same runtime models used by the installed application.

Keeping development preparation on the shared model manager prevents the
developer launcher from downloading an obsolete Whisper model or using a
different directory layout.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Developer models live in the repository; installed builds use LOCALAPPDATA.
os.environ.setdefault("RTL_MODELS_DIR", str(ROOT / "models"))


def main() -> int:
    try:
        from app.infrastructure.model_manager import ensure_models

        ensure_models(lambda message: print(message, flush=True))
        print("Local runtime models are ready.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Prepare the local models used by the Windows Preview.

Internet access is used only during this preparation step. The resulting
models are copied into the build tree and the packaged application runs
without network access.
"""
from __future__ import annotations

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRANSLATION_PAIRS = [
    ("en", "es"),
    ("es", "en"),
]

WHISPER_MODEL_MARKER = ROOT / "models" / "whisper" / "base" / "model.bin"
READY_MARKER = ROOT / "models" / ".ready"


def main() -> int:
    try:
        os.environ["ARGOS_PACKAGES_DIR"] = str(ROOT / "models" / "argos")

        from config.defaults import (
            DEFAULT_ASR_COMPUTE_TYPE,
            DEFAULT_ASR_DEVICE,
            DEFAULT_ASR_MODEL,
        )
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model

        model_dir = ROOT / "models" / "whisper" / DEFAULT_ASR_MODEL
        model_dir.mkdir(parents=True, exist_ok=True)

        if WHISPER_MODEL_MARKER.exists():
            print(f"Whisper model already present: {model_dir}")
        else:
            print(f"Downloading local Whisper model: {DEFAULT_ASR_MODEL}")
            local_path = download_model(DEFAULT_ASR_MODEL, output_dir=str(model_dir))
            print(f"Whisper model downloaded to: {local_path}")

        print("Verifying Whisper in local-only mode...")
        WhisperModel(
            str(model_dir),
            device=DEFAULT_ASR_DEVICE,
            compute_type=DEFAULT_ASR_COMPUTE_TYPE,
            local_files_only=True,
        )
        print("OK: Whisper local verification passed.")

        import argostranslate.package as package

        print("Checking local Argos translation packages...")
        package.update_package_index()
        available = package.get_available_packages()
        installed = {
            (p.from_code, p.to_code)
            for p in package.get_installed_packages()
            if p.type == "translate"
        }

        for source, target in TRANSLATION_PAIRS:
            if (source, target) in installed:
                print(f"OK: Argos {source}->{target} already installed")
                continue

            match = next(
                (
                    p
                    for p in available
                    if p.from_code == source and p.to_code == target
                ),
                None,
            )
            if match is None:
                raise RuntimeError(
                    f"Required Argos package {source}->{target} is unavailable."
                )

            print(f"Downloading/installing Argos package {source}->{target}...")
            package.install_from_path(match.download())

        portable_dir = ROOT / "models" / "argos"
        installed_after = {
            (p.from_code, p.to_code)
            for p in package.get_installed_packages()
            if p.type == "translate" and p.package_path.exists()
        }
        missing = [pair for pair in TRANSLATION_PAIRS if pair not in installed_after]
        if missing:
            raise RuntimeError(
                "Required Argos packages are not installed in the local model directory: "
                + ", ".join(f"{src}->{dst}" for src, dst in missing)
            )

        READY_MARKER.parent.mkdir(parents=True, exist_ok=True)
        READY_MARKER.write_text(
            "Real-Time Local Translator local models are ready.\n",
            encoding="utf-8",
        )

        print(f"Argos packages verified in: {portable_dir}")
        print(f"Model readiness marker created: {READY_MARKER}")
        print("Local model preparation completed.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

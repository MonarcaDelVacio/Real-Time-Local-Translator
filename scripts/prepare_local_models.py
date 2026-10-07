"""Prepare the local models used by the Windows Preview.

Internet access is used only during this preparation step. The resulting
models are copied into the build tree and the packaged application runs
without network access.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The first downloadable Preview intentionally focuses on the two directions
# needed for a complete end-to-end validation: English <-> Spanish.
TRANSLATION_PAIRS = [
    ("en", "es"),
    ("es", "en"),
]


def main() -> int:
    try:
        from config.defaults import (
            DEFAULT_ASR_COMPUTE_TYPE,
            DEFAULT_ASR_DEVICE,
            DEFAULT_ASR_MODEL,
        )
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model

        model_dir = ROOT / "models" / "whisper" / DEFAULT_ASR_MODEL
        model_dir.mkdir(parents=True, exist_ok=True)

        print(f"Preparing local Whisper model: {DEFAULT_ASR_MODEL}")
        local_path = download_model(DEFAULT_ASR_MODEL, output_dir=str(model_dir))
        print(f"Whisper model ready at: {local_path}")

        WhisperModel(
            str(model_dir),
            device=DEFAULT_ASR_DEVICE,
            compute_type=DEFAULT_ASR_COMPUTE_TYPE,
            local_files_only=True,
        )
        print("Whisper local verification passed.")

        import argostranslate.package as package

        print("Updating the Argos package index...")
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

            print(f"Installing local translation package {source}->{target}")
            package.install_from_path(match.download())

        portable_dir = ROOT / "models" / "argos"
        portable_dir.mkdir(parents=True, exist_ok=True)

        for pkg in package.get_installed_packages():
            if pkg.type != "translate" or not pkg.package_path.exists():
                continue
            destination = portable_dir / pkg.package_path.name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(pkg.package_path, destination)

        print(f"Portable Argos packages copied to: {portable_dir}")
        print("Local model preparation completed.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

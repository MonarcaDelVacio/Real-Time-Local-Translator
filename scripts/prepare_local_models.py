"""Prepare local models. Internet is used only during this one-time setup."""
from __future__ import annotations

from pathlib import Path

TRANSLATION_PAIRS = [
    ("en", "es"), ("es", "en"), ("en", "pt"), ("pt", "en"),
    ("en", "fr"), ("fr", "en"), ("en", "de"), ("de", "en"),
    ("en", "it"), ("it", "en"), ("en", "ja"), ("ja", "en"),
    ("en", "ko"), ("ko", "en"), ("en", "zh"), ("zh", "en"),
]


def main() -> int:
    try:
        from config.defaults import DEFAULT_ASR_COMPUTE_TYPE, DEFAULT_ASR_DEVICE, DEFAULT_ASR_MODEL
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model

        model_dir = Path("models") / "whisper" / DEFAULT_ASR_MODEL
        model_dir.mkdir(parents=True, exist_ok=True)
        print(f"Preparing local Whisper model: {DEFAULT_ASR_MODEL}")
        local_path = download_model(
            DEFAULT_ASR_MODEL,
            output_dir=str(model_dir),
            local_files_only=False,
        )
        print(f"Whisper model ready at: {local_path}")

        # Load once now to verify the local CTranslate2 model and runtime compute type.
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
                (p for p in available if p.from_code == source and p.to_code == target),
                None,
            )
            if match is None:
                print(f"SKIP: no package available for {source}->{target}")
                continue
            print(f"Installing local translation package {source}->{target}")
            package.install_from_path(match.download())

        print("Local model preparation completed.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

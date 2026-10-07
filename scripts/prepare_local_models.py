"""Prepare all models locally. Network is used only during this one-time setup."""
from __future__ import annotations

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

        print(f"Preparing local Whisper model: {DEFAULT_ASR_MODEL}")
        WhisperModel(DEFAULT_ASR_MODEL, device=DEFAULT_ASR_DEVICE, compute_type=DEFAULT_ASR_COMPUTE_TYPE)
        print("Whisper model is cached locally.")

        import argostranslate.package as package
        print("Updating the Argos package index...")
        package.update_package_index()
        available = package.get_available_packages()
        for source, target in TRANSLATION_PAIRS:
            match = next((p for p in available if p.from_code == source and p.to_code == target), None)
            if match is None:
                print(f"SKIP: no package available for {source}->{target}")
                continue
            print(f"Installing local translation package {source}->{target}")
            package.install_from_path(match.download())

        print("All available requested local packages are prepared.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

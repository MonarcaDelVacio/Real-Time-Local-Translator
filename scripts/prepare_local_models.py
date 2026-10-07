"""Download local models/packages once during setup.

This script uses the network only for initial installation. Runtime translation is local.
"""
from __future__ import annotations
import sys

TRANSLATION_PAIRS = [("en", "es"), ("es", "en"), ("en", "pt"), ("pt", "en"), ("en", "fr"), ("fr", "en"), ("en", "de"), ("de", "en"), ("en", "it"), ("it", "en"), ("en", "ja"), ("ja", "en"), ("en", "ko"), ("ko", "en"), ("en", "zh"), ("zh", "en")]

def main() -> int:
    try:
        from faster_whisper import WhisperModel
        from config.defaults import DEFAULT_ASR_MODEL, DEFAULT_ASR_DEVICE, DEFAULT_ASR_COMPUTE_TYPE
        print(f"Preparing Whisper model: {DEFAULT_ASR_MODEL}")
        WhisperModel(DEFAULT_ASR_MODEL, device=DEFAULT_ASR_DEVICE, compute_type=DEFAULT_ASR_COMPUTE_TYPE)
        print("Whisper model ready in the local cache.")

        import argostranslate.package as package
        import argostranslate.translate as translate
        package.update_package_index()
        available = package.get_available_packages()
        installed = {(x.from_code, x.to_code) for x in translate.get_installed_languages() for _ in []}
        for source, target in TRANSLATION_PAIRS:
            match = next((p for p in available if p.from_code == source and p.to_code == target), None)
            if match is None:
                print(f"SKIP: no Argos package {source}->{target}")
                continue
            print(f"Installing Argos package {source}->{target}")
            package.install_from_path(match.download())
        print("Local language packages prepared.")
        return 0
    except Exception as exc:
        print(f"SETUP ERROR: {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

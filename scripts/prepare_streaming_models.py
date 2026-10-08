from pathlib import Path
import os
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = "nemotron-3.5-asr-streaming-0.6b-560ms-int8-2026-06-11"
URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-" + MODEL + ".tar.bz2"

def main():
    model_root = ROOT / "models" / "sherpa"
    model_dir = model_root / MODEL
    model_root.mkdir(parents=True, exist_ok=True)

    required = [model_dir / n for n in (
        "encoder.int8.onnx", "decoder.int8.onnx",
        "joiner.int8.onnx", "tokens.txt"
    )]
    if not all(p.is_file() for p in required):
        archive = model_root / (MODEL + ".tar.bz2")
        print("Downloading Sherpa streaming model...")
        urllib.request.urlretrieve(URL, archive)
        print("Extracting Sherpa streaming model...")
        with tarfile.open(archive, "r:bz2") as tar:
            tar.extractall(model_root)
        archive.unlink(missing_ok=True)

    if not all(p.is_file() for p in required):
        raise RuntimeError("Sherpa streaming model is incomplete.")

    os.environ["ARGOS_PACKAGES_DIR"] = str(ROOT / "models" / "argos")
    import argostranslate.package as package
    package.update_package_index()
    available = package.get_available_packages()
    wanted = {("en", "es"), ("es", "en")}
    installed = {
        (p.from_code, p.to_code)
        for p in package.get_installed_packages()
        if p.type == "translate"
    }
    for src, dst in wanted - installed:
        match = next((p for p in available if p.from_code == src and p.to_code == dst), None)
        if match is None:
            raise RuntimeError(f"Argos package unavailable: {src}->{dst}")
        print(f"Installing Argos {src}->{dst}...")
        package.install_from_path(match.download())

    (ROOT / "models" / ".ready").write_text("streaming models ready\n", encoding="utf-8")
    print("Local streaming models are ready.")

if __name__ == "__main__":
    main()

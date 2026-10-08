from pathlib import Path
import os
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
MODEL = "nemotron-3.5-asr-streaming-0.6b-1120ms-int8-2026-06-11"
WHISPER_MODEL = "Systran/faster-whisper-small"
ARCHIVE_NAME = f"sherpa-onnx-{MODEL}.tar.bz2"
URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    f"asr-models/{ARCHIVE_NAME}"
)
REQUIRED_NAMES = (
    "encoder.int8.onnx",
    "decoder.int8.onnx",
    "joiner.int8.onnx",
    "tokens.txt",
)


def _required(directory: Path) -> list[Path]:
    return [directory / name for name in REQUIRED_NAMES]


def _find_model_directory(root: Path) -> Path | None:
    direct = root / MODEL
    if all(p.is_file() for p in _required(direct)):
        return direct
    for tokens in root.rglob("tokens.txt"):
        candidate = tokens.parent
        if all(p.is_file() for p in _required(candidate)):
            return candidate
    return None


def _download(archive: Path) -> None:
    print(f"Downloading {ARCHIVE_NAME} from the official Sherpa-ONNX release...")
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl.exe is required to download the Sherpa model.")
    if archive.exists():
        archive.unlink()
    subprocess.run(
        [
            curl,
            "--fail",
            "--location",
            "--retry",
            "5",
            "--retry-delay",
            "5",
            "--retry-all-errors",
            "--continue-at",
            "-",
            "--output",
            str(archive),
            URL,
        ],
        check=True,
    )
    size = archive.stat().st_size
    print(f"Downloaded archive size: {size / (1024 * 1024):.1f} MiB")
    if size < 50_000_000:
        raise RuntimeError("Downloaded Sherpa archive is unexpectedly small or incomplete.")


def _extract(archive: Path, model_root: Path) -> Path:
    print("Extracting Sherpa streaming model...")
    with tarfile.open(archive, "r:bz2") as tar:
        tar.extractall(model_root)
    found = _find_model_directory(model_root)
    if found is None:
        raise RuntimeError(
            "Sherpa archive extracted successfully, but the expected ONNX files could not be found."
        )
    model_dir = model_root / MODEL
    if found.resolve() != model_dir.resolve():
        if model_dir.exists():
            shutil.rmtree(model_dir)
        shutil.copytree(found, model_dir)
    return model_dir


def main() -> None:
    model_root = ROOT / "models" / "sherpa"
    model_dir = model_root / MODEL
    model_root.mkdir(parents=True, exist_ok=True)

    if not all(p.is_file() for p in _required(model_dir)):
        archive = model_root / ARCHIVE_NAME
        try:
            _download(archive)
            _extract(archive, model_root)
        finally:
            archive.unlink(missing_ok=True)

    if not all(p.is_file() for p in _required(model_dir)):
        raise RuntimeError("Sherpa streaming model is incomplete after extraction.")

    print("Sherpa model files validated.")
    whisper_root = ROOT / "models" / "whisper" / "small"
    if not (whisper_root / "model.bin").is_file():
        print(f"Downloading local Whisper refinement model: {WHISPER_MODEL}...")
        from huggingface_hub import snapshot_download
        snapshot_download(repo_id=WHISPER_MODEL, local_dir=str(whisper_root))
    if not (whisper_root / "model.bin").is_file():
        raise RuntimeError("Whisper refinement model is incomplete after download.")
    print("Whisper refinement model validated.")
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
        match = next(
            (p for p in available if p.from_code == src and p.to_code == dst),
            None,
        )
        if match is None:
            raise RuntimeError(f"Argos package unavailable: {src}->{dst}")
        print(f"Installing Argos {src}->{dst}...")
        package.install_from_path(match.download())

    (ROOT / "models" / ".ready").write_text(
        "streaming models ready\n",
        encoding="utf-8",
    )
    print("Local streaming models are ready.")


if __name__ == "__main__":
    main()

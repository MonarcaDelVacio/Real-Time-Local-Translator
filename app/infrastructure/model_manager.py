from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tarfile

from app.infrastructure.paths import models_root

MODEL = "nemotron-3.5-asr-streaming-0.6b-1120ms-int8-2026-06-11"
WHISPER_MODEL = "Systran/faster-whisper-small"
SHERPA_ARCHIVE = f"sherpa-onnx-{MODEL}.tar.bz2"
SHERPA_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    f"asr-models/{SHERPA_ARCHIVE}"
)
SHERPA_REQUIRED = ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt")
WHISPER_REQUIRED = ("config.json", "model.bin", "preprocessor_config.json", "tokenizer.json")
ARGOS_REQUIRED = (("en", "es"), ("es", "en"))


def _complete(path: Path, names: tuple[str, ...]) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in names)


def models_ready() -> bool:
    root = models_root()
    sherpa = root / "sherpa" / MODEL
    whisper = root / "whisper" / "small"
    if not _complete(sherpa, SHERPA_REQUIRED) or not _complete(whisper, WHISPER_REQUIRED):
        return False
    try:
        import argostranslate.package as package
        installed = {(p.from_code, p.to_code) for p in package.get_installed_packages() if p.type == "translate"}
        return all(pair in installed for pair in ARGOS_REQUIRED)
    except Exception:
        return False


def _download_sherpa(destination: Path, status) -> None:
    import urllib.request
    root = destination.parent
    root.mkdir(parents=True, exist_ok=True)
    archive = root / SHERPA_ARCHIVE
    status("Descargando modelo ASR streaming desde GitHub (Sherpa-ONNX)…")
    urllib.request.urlretrieve(SHERPA_URL, archive)
    status("Extrayendo modelo ASR streaming…")
    with tarfile.open(archive, "r:bz2") as tar:
        tar.extractall(root)
    archive.unlink(missing_ok=True)
    if not _complete(destination, SHERPA_REQUIRED):
        found = next((p.parent for p in root.rglob("tokens.txt") if _complete(p.parent, SHERPA_REQUIRED)), None)
        if found is None:
            raise RuntimeError("El modelo Sherpa-ONNX se descargó, pero está incompleto.")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(found, destination)


def ensure_models(status=lambda _: None) -> None:
    """Verify every runtime model and repair missing/incomplete files online."""
    root = models_root()
    root.mkdir(parents=True, exist_ok=True)
    sherpa = root / "sherpa" / MODEL
    whisper = root / "whisper" / "small"

    if not _complete(sherpa, SHERPA_REQUIRED):
        _download_sherpa(sherpa, status)
    if not _complete(sherpa, SHERPA_REQUIRED):
        raise RuntimeError("El modelo Sherpa-ONNX sigue incompleto después de la descarga.")
    status("Modelo ASR streaming verificado.")

    if not _complete(whisper, WHISPER_REQUIRED):
        status("Descargando modelo Whisper de refinamiento…")
        from huggingface_hub import snapshot_download
        whisper.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=WHISPER_MODEL,
            local_dir=str(whisper),
            allow_patterns=list(WHISPER_REQUIRED),
        )
    missing = [name for name in WHISPER_REQUIRED if not (whisper / name).is_file()]
    if missing:
        raise RuntimeError("El modelo Whisper está incompleto; faltan: " + ", ".join(missing))
    status("Modelo Whisper verificado.")

    import os
    os.environ["ARGOS_PACKAGES_DIR"] = str(root / "argos")
    import argostranslate.package as package
    status("Verificando paquetes de traducción Argos…")
    package.update_package_index()
    available = package.get_available_packages()
    installed = {(p.from_code, p.to_code) for p in package.get_installed_packages() if p.type == "translate"}
    for src, dst in ARGOS_REQUIRED:
        if (src, dst) in installed:
            continue
        match = next((p for p in available if p.from_code == src and p.to_code == dst), None)
        if match is None:
            raise RuntimeError(f"El paquete Argos {src}->{dst} no está disponible.")
        status(f"Descargando traducción Argos {src} → {dst}…")
        package.install_from_path(match.download())

    installed = {(p.from_code, p.to_code) for p in package.get_installed_packages() if p.type == "translate" and p.package_path.exists()}
    missing = [f"{src}->{dst}" for src, dst in ARGOS_REQUIRED if (src, dst) not in installed]
    if missing:
        raise RuntimeError("Paquetes Argos faltantes: " + ", ".join(missing))
    (root / ".ready").write_text("runtime models ready\n", encoding="utf-8")
    status("Todos los modelos y paquetes locales están listos.")

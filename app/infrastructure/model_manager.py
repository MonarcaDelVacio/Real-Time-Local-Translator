from __future__ import annotations

import json
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath

from app.infrastructure.paths import models_root

MODEL = "nemotron-3.5-asr-streaming-0.6b-1120ms-int8-2026-06-11"
WHISPER_MODEL = "Systran/faster-whisper-small"
SHERPA_ARCHIVE = f"sherpa-onnx-{MODEL}.tar.bz2"
SHERPA_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    f"asr-models/{SHERPA_ARCHIVE}"
)
SHERPA_REQUIRED = ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt")
WHISPER_REQUIRED = (
    "config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.txt",
    "preprocessor_config.json",
)
ARGOS_REQUIRED = (("en", "es"), ("es", "en"))


def _ensure_gui_stdio() -> None:
    """Give console-oriented libraries writable streams in windowed builds."""
    import io
    import sys

    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()


def _complete(path: Path, names: tuple[str, ...]) -> bool:
    return path.is_dir() and all(
        (path / name).is_file() and (path / name).stat().st_size > 0
        for name in names
    )


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    """Extract regular files/directories only and reject paths escaping destination."""
    root = destination.resolve()
    members = archive.getmembers()
    for member in members:
        member_path = PurePosixPath(member.name)
        if member_path.is_absolute() or ".." in member_path.parts or "\\" in member.name or (member_path.parts and ":" in member_path.parts[0]):
            raise RuntimeError(f"Archivo de modelo contiene una ruta insegura: {member.name}")
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise RuntimeError(f"Archivo de modelo contiene un tipo de entrada no permitido: {member.name}")
        target = (destination / Path(*member_path.parts)).resolve()
        if target != root and root not in target.parents:
            raise RuntimeError(f"Archivo de modelo intenta salir de la carpeta destino: {member.name}")
    archive.extractall(destination, members=members)


def _download_archive(url: str, destination: Path, status) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    try:
        status("Descargando modelo ASR streaming desde GitHub (Sherpa-ONNX)…")
        with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as out:
            total = int(response.headers.get("Content-Length", "0") or "0")
            downloaded = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
                downloaded += len(block)
                if total > 0:
                    status(f"Descargando modelo Sherpa-ONNX… {downloaded * 100 // total}%")
        if not temporary.is_file() or temporary.stat().st_size < 50_000_000:
            raise RuntimeError("La descarga del modelo Sherpa-ONNX está incompleta o es demasiado pequeña.")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _download_sherpa(destination: Path, status) -> None:
    root = destination.parent
    root.mkdir(parents=True, exist_ok=True)
    archive_path = root / SHERPA_ARCHIVE
    staging = root / f".{MODEL}.extracting"
    try:
        _download_archive(SHERPA_URL, archive_path, status)
        status("Verificando y extrayendo el modelo ASR streaming…")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        with tarfile.open(archive_path, "r:bz2") as archive:
            _safe_extract(archive, staging)

        found = next(
            (p.parent for p in staging.rglob("tokens.txt") if _complete(p.parent, SHERPA_REQUIRED)),
            None,
        )
        if found is None:
            raise RuntimeError("El modelo Sherpa-ONNX se descargó, pero está incompleto.")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(found, destination)
        if not _complete(destination, SHERPA_REQUIRED):
            raise RuntimeError("El modelo Sherpa-ONNX no superó la verificación posterior a la extracción.")
    finally:
        archive_path.unlink(missing_ok=True)
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _argos_installed_pairs(root: Path) -> set[tuple[str, str]]:
    os.environ["ARGOS_PACKAGES_DIR"] = str(root / "argos")
    from argostranslate import package

    return {
        (item.from_code, item.to_code)
        for item in package.get_installed_packages()
        if item.type == "translate" and Path(item.package_path).exists()
    }


def models_ready() -> bool:
    _ensure_gui_stdio()
    root = models_root()
    if not _complete(root / "sherpa" / MODEL, SHERPA_REQUIRED):
        return False
    whisper = root / "whisper" / "small"
    if not _complete(whisper, WHISPER_REQUIRED):
        return False
    try:
        # Catch partial/corrupt JSON before enabling the Start button.
        json.loads((whisper / "config.json").read_text(encoding="utf-8"))
        json.loads((whisper / "preprocessor_config.json").read_text(encoding="utf-8"))
        return set(ARGOS_REQUIRED).issubset(_argos_installed_pairs(root))
    except Exception:
        return False


def ensure_models(status=lambda _: None) -> None:
    """Verify every runtime model and repair missing/incomplete files online."""
    _ensure_gui_stdio()
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
        status("Descargando o reparando el modelo Whisper de refinamiento…")
        from huggingface_hub import snapshot_download

        whisper.parent.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=WHISPER_MODEL,
            local_dir=str(whisper),
            allow_patterns=list(WHISPER_REQUIRED),
        )
    missing = [name for name in WHISPER_REQUIRED if not (whisper / name).is_file() or (whisper / name).stat().st_size == 0]
    if missing:
        raise RuntimeError("El modelo Whisper está incompleto; faltan: " + ", ".join(missing))
    try:
        json.loads((whisper / "config.json").read_text(encoding="utf-8"))
        json.loads((whisper / "preprocessor_config.json").read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"La configuración local de Whisper está dañada: {exc}") from exc
    status("Modelo Whisper verificado.")

    os.environ["ARGOS_PACKAGES_DIR"] = str(root / "argos")
    from argostranslate import package

    status("Verificando paquetes de traducción Argos…")
    installed = _argos_installed_pairs(root)
    if not set(ARGOS_REQUIRED).issubset(installed):
        package.update_package_index()
        available = package.get_available_packages()
        for src, dst in ARGOS_REQUIRED:
            if (src, dst) in installed:
                continue
            match = next((item for item in available if item.from_code == src and item.to_code == dst), None)
            if match is None:
                raise RuntimeError(f"El paquete Argos {src}->{dst} no está disponible en el índice.")
            status(f"Descargando traducción Argos {src} → {dst}…")
            package.install_from_path(match.download())

    installed = _argos_installed_pairs(root)
    missing_pairs = [f"{src}->{dst}" for src, dst in ARGOS_REQUIRED if (src, dst) not in installed]
    if missing_pairs:
        raise RuntimeError("Paquetes Argos faltantes o incompletos: " + ", ".join(missing_pairs))

    (root / ".ready").write_text("runtime models ready\n", encoding="utf-8")
    status("Todos los modelos y paquetes locales están listos.")

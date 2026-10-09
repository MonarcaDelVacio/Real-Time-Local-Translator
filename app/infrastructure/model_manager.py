from __future__ import annotations

import json
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath

from app.infrastructure.paths import bundled_models_root, models_root

MODEL = "nemotron-3.5-asr-streaming-0.6b-560ms-int8-2026-06-11"
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
)
ARGOS_REQUIRED = (("en", "es"), ("es", "en"))
SHERPA_MIN_BYTES = {
    "encoder.int8.onnx": 1_000_000,
    "decoder.int8.onnx": 100_000,
    "joiner.int8.onnx": 100_000,
    "tokens.txt": 100,
}
WHISPER_MIN_BYTES = {
    "config.json": 100,
    "model.bin": 100_000_000,
    "tokenizer.json": 1_000,
    "vocabulary.txt": 100,
}


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


def _assets_complete(path: Path, minimum_sizes: dict[str, int]) -> bool:
    """Reject missing, empty, or suspiciously truncated required model files."""
    return path.is_dir() and all(
        (path / name).is_file() and (path / name).stat().st_size >= minimum
        for name, minimum in minimum_sizes.items()
    )


def _whisper_config_valid(path: Path) -> bool:
    """Return whether the local CTranslate2 config is readable JSON object data."""
    try:
        value = json.loads((path / "config.json").read_text(encoding="utf-8"))
        return isinstance(value, dict) and bool(value)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False


def _seed_bundled_models(root: Path) -> None:
    """Copy complete bundled model assets into the writable per-user directory."""
    source = bundled_models_root()
    if source is None or source.resolve() == root.resolve():
        return
    for relative, required in (
        (Path("sherpa") / MODEL, SHERPA_REQUIRED),
        (Path("whisper") / "small", WHISPER_REQUIRED),
    ):
        bundled = source / relative
        destination = root / relative
        if _complete(destination, required):
            continue
        if _complete(bundled, required):
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(bundled, destination)
    bundled_argos = source / "argos"
    destination_argos = root / "argos"
    if bundled_argos.is_dir():
        try:
            argos_is_ready = _argos_translations_ready(root)
        except Exception:
            argos_is_ready = False
        if not argos_is_ready:
            if destination_argos.exists():
                shutil.rmtree(destination_argos, ignore_errors=True)
            destination_argos.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(bundled_argos, destination_argos)


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
    import time

    temporary = destination.with_suffix(destination.suffix + ".part")
    last_error: Exception | None = None
    for attempt in range(1, 4):
        temporary.unlink(missing_ok=True)
        try:
            status(f"Descargando modelo ASR streaming desde GitHub (intento {attempt}/3)…")
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
            if total > 0 and downloaded != total:
                raise RuntimeError(
                    f"Descarga incompleta del modelo Sherpa-ONNX: {downloaded} de {total} bytes."
                )
            if not temporary.is_file() or temporary.stat().st_size < 50_000_000:
                raise RuntimeError("La descarga del modelo Sherpa-ONNX está incompleta o es demasiado pequeña.")
            temporary.replace(destination)
            return
        except Exception as exc:
            last_error = exc
            temporary.unlink(missing_ok=True)
            if attempt < 3:
                status(f"La descarga falló; se volverá a intentar ({attempt}/3).")
                time.sleep(2 * attempt)
    raise RuntimeError(f"No se pudo descargar el modelo Sherpa-ONNX tras 3 intentos: {last_error}") from last_error

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
            (p.parent for p in staging.rglob("tokens.txt") if _assets_complete(p.parent, SHERPA_MIN_BYTES)),
            None,
        )
        if found is None:
            raise RuntimeError("El modelo Sherpa-ONNX se descargó, pero está incompleto.")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(found, destination)
        if not _assets_complete(destination, SHERPA_MIN_BYTES):
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


def _argos_translations_ready(root: Path) -> bool:
    _argos_installed_pairs(root)
    from argostranslate import translate

    return all(
        translate.get_translation_from_codes(source, target) is not None
        for source, target in ARGOS_REQUIRED
    )


def _argos_ready_pairs(root: Path) -> set[tuple[str, str]]:
    """Return the required Argos directions that can actually be loaded."""
    os.environ["ARGOS_PACKAGES_DIR"] = str(root / "argos")
    from argostranslate import translate

    ready = set()
    for source, target in ARGOS_REQUIRED:
        try:
            if translate.get_translation_from_codes(source, target) is not None:
                ready.add((source, target))
        except Exception:
            # One corrupt package must not hide the status of the other direction.
            continue
    return ready


def _remove_argos_installation(root: Path, pair: tuple[str, str], installed_packages) -> bool:
    """Remove only the broken package for this app, never a path outside its Argos folder."""
    package_root = (root / "argos").resolve()
    for item in installed_packages:
        if (getattr(item, "from_code", None), getattr(item, "to_code", None)) != pair:
            continue
        raw_path = getattr(item, "package_path", None)
        if not raw_path:
            continue
        path = Path(raw_path).resolve()
        if path == package_root or package_root not in path.parents:
            continue
        if path.is_dir():
            shutil.rmtree(path)
            return True
        if path.is_file():
            path.unlink()
            return True
    return False


def models_ready() -> bool:
    _ensure_gui_stdio()
    root = models_root()
    if not _assets_complete(root / "sherpa" / MODEL, SHERPA_MIN_BYTES):
        return False
    whisper = root / "whisper" / "small"
    if not _assets_complete(whisper, WHISPER_MIN_BYTES) or not _whisper_config_valid(whisper):
        return False
    try:
        return _argos_translations_ready(root)
    except Exception:
        return False


def ensure_models(status=lambda _: None) -> None:
    """Verify every runtime model and repair missing/incomplete files online."""
    _ensure_gui_stdio()
    root = models_root()
    root.mkdir(parents=True, exist_ok=True)
    _seed_bundled_models(root)
    sherpa = root / "sherpa" / MODEL
    whisper = root / "whisper" / "small"

    if not _assets_complete(sherpa, SHERPA_MIN_BYTES):
        _download_sherpa(sherpa, status)
    if not _assets_complete(sherpa, SHERPA_MIN_BYTES):
        raise RuntimeError("El modelo Sherpa-ONNX sigue incompleto después de la descarga.")
    status("Modelo ASR streaming verificado.")

    if not _assets_complete(whisper, WHISPER_MIN_BYTES) or not _whisper_config_valid(whisper):
        status("Descargando o reparando el modelo Whisper de refinamiento…")
        from huggingface_hub import snapshot_download

        whisper.parent.mkdir(parents=True, exist_ok=True)
        # A malformed config must not be treated as a complete local snapshot.
        # force_download also repairs required files that exist but were truncated.
        snapshot_download(
            repo_id=WHISPER_MODEL,
            local_dir=str(whisper),
            allow_patterns=list(WHISPER_REQUIRED),
            force_download=True,
        )
    missing = [
        name for name, minimum in WHISPER_MIN_BYTES.items()
        if not (whisper / name).is_file() or (whisper / name).stat().st_size < minimum
    ]
    if missing:
        raise RuntimeError(
            "El modelo Whisper está incompleto o parece truncado; faltan o son demasiado pequeños: "
            + ", ".join(missing)
        )
    if not _whisper_config_valid(whisper):
        raise RuntimeError("La configuración local de Whisper sigue dañada después de intentar repararla.")
    status("Modelo Whisper verificado.")

    os.environ["ARGOS_PACKAGES_DIR"] = str(root / "argos")
    from argostranslate import package

    status("Verificando paquetes de traducción Argos…")
    try:
        installed = _argos_installed_pairs(root)
        ready = _argos_ready_pairs(root)
    except Exception as exc:
        # This folder is dedicated to this app's currently supported en/es
        # packages. If Argos cannot even enumerate it, rebuild that folder and
        # let the normal package installer restore both required directions.
        status(f"Instalación de Argos dañada; se reconstruirá: {exc}")
        shutil.rmtree(root / "argos", ignore_errors=True)
        (root / "argos").mkdir(parents=True, exist_ok=True)
        installed = set()
        ready = set()

    # A package can be listed as installed while its model files are unusable.
    # Remove only that app-managed package and reinstall the missing direction.
    broken = [pair for pair in ARGOS_REQUIRED if pair in installed and pair not in ready]
    if broken:
        installed_packages = package.get_installed_packages()
        for pair in broken:
            if not _remove_argos_installation(root, pair, installed_packages):
                source, target = pair
                raise RuntimeError(
                    f"Argos {source}->{target} figura instalado pero no puede cargarse, "
                    "y su archivo no está dentro de la carpeta de modelos de esta aplicación. "
                    "El paquete debe repararse manualmente."
                )
        installed = _argos_installed_pairs(root)
        ready = _argos_ready_pairs(root)

    missing_pairs = [pair for pair in ARGOS_REQUIRED if pair not in ready]
    if missing_pairs:
        package.update_package_index()
        available = package.get_available_packages()
        for src, dst in missing_pairs:
            match = next((item for item in available if item.from_code == src and item.to_code == dst), None)
            if match is None:
                raise RuntimeError(f"El paquete Argos {src}->{dst} no está disponible en el índice.")
            status(f"Descargando o reparando traducción Argos {src} → {dst}…")
            package.install_from_path(match.download())

    ready = _argos_ready_pairs(root)
    missing_pairs = [f"{src}->{dst}" for src, dst in ARGOS_REQUIRED if (src, dst) not in ready]
    if missing_pairs:
        raise RuntimeError("Paquetes Argos faltantes o inutilizables: " + ", ".join(missing_pairs))

    (root / ".ready").write_text("runtime models ready\n", encoding="utf-8")
    status("Todos los modelos y paquetes locales están listos.")

import io
import tarfile
from types import SimpleNamespace

import pytest

from app.infrastructure.model_manager import WHISPER_REQUIRED, _assets_complete, _complete, _remove_argos_installation, _safe_extract, _status_tqdm_class, _whisper_config_valid


def test_complete_rejects_empty_required_files(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "weights.bin").write_bytes(b"")
    assert not _complete(model, ("weights.bin",))
    (model / "weights.bin").write_bytes(b"weights")
    assert _complete(model, ("weights.bin",))


def test_safe_extract_rejects_parent_traversal(tmp_path):
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:bz2") as archive:
        payload = b"unsafe"
        info = tarfile.TarInfo("../outside.txt")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    archive_bytes.seek(0)
    destination = tmp_path / "extracted"
    destination.mkdir()
    with tarfile.open(fileobj=archive_bytes, mode="r:bz2") as archive:
        with pytest.raises(RuntimeError, match="ruta insegura"):
            _safe_extract(archive, destination)
    assert not (tmp_path / "outside.txt").exists()


def test_safe_extract_accepts_regular_file(tmp_path):
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:bz2") as archive:
        payload = b"model-data"
        info = tarfile.TarInfo("model/weights.bin")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    archive_bytes.seek(0)
    destination = tmp_path / "extracted"
    destination.mkdir()
    with tarfile.open(fileobj=archive_bytes, mode="r:bz2") as archive:
        _safe_extract(archive, destination)
    assert (destination / "model" / "weights.bin").read_bytes() == b"model-data"


def test_official_faster_whisper_small_files_are_sufficient(tmp_path):
    model = tmp_path / "small"
    model.mkdir()
    for name in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt"):
        (model / name).write_bytes(b"valid")
    assert "preprocessor_config.json" not in WHISPER_REQUIRED
    assert _complete(model, WHISPER_REQUIRED)


def test_whisper_config_validator_rejects_corrupt_or_non_object_json(tmp_path):
    model = tmp_path / "small"
    model.mkdir()
    config = model / "config.json"
    config.write_text("{broken", encoding="utf-8")
    assert not _whisper_config_valid(model)
    config.write_text("[]", encoding="utf-8")
    assert not _whisper_config_valid(model)
    config.write_text('{"model_type": "whisper"}', encoding="utf-8")
    assert _whisper_config_valid(model)


def test_remove_argos_installation_only_removes_package_inside_app_model_root(tmp_path):
    root = tmp_path / "models"
    package_dir = root / "argos" / "translate-en_es"
    package_dir.mkdir(parents=True)
    (package_dir / "package.toml").write_text("broken", encoding="utf-8")
    installed = [
        SimpleNamespace(
            from_code="en",
            to_code="es",
            package_path=str(package_dir),
        )
    ]

    assert _remove_argos_installation(root, ("en", "es"), installed)
    assert not package_dir.exists()


def test_remove_argos_installation_refuses_external_package_path(tmp_path):
    root = tmp_path / "models"
    external = tmp_path / "external-package"
    external.mkdir()
    installed = [
        SimpleNamespace(
            from_code="en",
            to_code="es",
            package_path=str(external),
        )
    ]

    assert not _remove_argos_installation(root, ("en", "es"), installed)
    assert external.exists()


def test_assets_complete_rejects_nonempty_but_truncated_model_file(tmp_path):
    model = tmp_path / "whisper"
    model.mkdir()
    weights = model / "model.bin"
    weights.write_bytes(b"short but nonempty")

    assert _complete(model, ("model.bin",))
    assert not _assets_complete(model, {"model.bin": 100})

    weights.write_bytes(b"x" * 100)
    assert _assets_complete(model, {"model.bin": 100})


def test_huggingface_progress_is_forwarded_to_setup_status():
    messages = []
    progress_type = _status_tqdm_class(messages.append)
    progress = progress_type(total=100, file=io.StringIO(), mininterval=0, leave=False)
    try:
        progress.update(25)
        progress.update(25)
        progress.update(50)
    finally:
        progress.close()

    assert any("25%" in message for message in messages)
    assert any("50%" in message for message in messages)
    assert messages[-1].startswith("Descargando Whisper… 100%")

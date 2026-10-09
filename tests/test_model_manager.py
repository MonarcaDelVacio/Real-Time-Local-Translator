import io
import tarfile

import pytest

from app.infrastructure.model_manager import WHISPER_REQUIRED, _complete, _safe_extract


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

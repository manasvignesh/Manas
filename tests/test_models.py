import hashlib

import pytest

from manas.models.catalog import ModelCatalogEntry, load_catalog, recommend
from manas.models.discovery import detect_models, inspect_system
from manas.models.downloader import ChecksumError, download_model
from manas.utils.config import AppConfig


def test_gguf_discovery_and_system_inspection(tmp_path):
    model = tmp_path / "tiny.gguf"
    model.write_bytes(b"GGUF")
    found = detect_models(AppConfig(model_paths=[str(model)]))
    assert any(item.location == str(model.resolve()) for item in found)
    profile = inspect_system()
    assert profile.cpu_threads >= 1
    assert profile.disk_free_bytes > 0


def test_catalog_is_valid_and_recommends_a_fit():
    catalog = load_catalog()
    selected = recommend(catalog, 8 * 1024 ** 3)
    assert catalog
    assert selected.minimum_ram_gb <= 8
    assert selected.download_url.startswith("https://")
    assert len(selected.sha256) == 64


class FakeResponse:
    def __init__(self, content: bytes, status: int = 200):
        self.content = content
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, _size: int = -1) -> bytes:
        content, self.content = self.content, b""
        return content


def catalog_entry(content: bytes) -> ModelCatalogEntry:
    return ModelCatalogEntry(
        id="test-model",
        display_name="Test model",
        provider="llama.cpp",
        parameters="tiny",
        quantization="Q4",
        download_url="https://example.invalid/model.gguf",
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        minimum_ram_gb=1,
        recommended_ram_gb=1,
        license="test-only",
        description="Fixture",
    )


def test_download_validates_checksum_and_atomically_finishes(tmp_path):
    content = b"GGUF-test-payload"
    output = download_model(catalog_entry(content), tmp_path, opener=lambda *_args, **_kwargs: FakeResponse(content))
    assert output.read_bytes() == content
    assert not (tmp_path / ".test-model.gguf.part").exists()


def test_download_resumes_partial_content(tmp_path):
    content = b"GGUF-resumable"
    partial = tmp_path / ".test-model.gguf.part"
    partial.write_bytes(content[:4])
    requests = []

    def opener(request, **_kwargs):
        requests.append(request)
        return FakeResponse(content[4:], status=206)

    output = download_model(catalog_entry(content), tmp_path, opener=opener)
    assert output.read_bytes() == content
    assert requests[0].get_header("Range") == "bytes=4-"


def test_bad_checksum_preserves_partial_file(tmp_path):
    expected = b"expected"
    with pytest.raises(ChecksumError):
        download_model(catalog_entry(expected), tmp_path, opener=lambda *_args, **_kwargs: FakeResponse(b"corrupt"))
    assert (tmp_path / ".test-model.gguf.part").read_bytes() == b"corrupt"

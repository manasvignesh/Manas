from manas.models.discovery import detect_models, inspect_system
from manas.utils.config import AppConfig


def test_gguf_discovery_and_system_inspection(tmp_path):
    model = tmp_path / "tiny.gguf"
    model.write_bytes(b"GGUF")
    found = detect_models(AppConfig(model_paths=[str(model)]))
    assert any(item.location == str(model.resolve()) for item in found)
    profile = inspect_system()
    assert profile.cpu_threads >= 1
    assert profile.disk_free_bytes > 0

from __future__ import annotations

import os
import json
import shutil
from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    default_population_size: int = Field(default=100, ge=1)
    default_region: str = "India"
    reasoning_engine: str = "none"
    default_seed: int = 42
    storage_path: str = ""
    model_paths: list[str] = Field(default_factory=list)
    active_model_path: str = ""
    color: bool = True
    log_level: str = "WARNING"


def home_dir() -> Path:
    override = os.environ.get("MANAS_HOME") or os.environ.get("CROWDFORGE_HOME")
    return Path(override).expanduser() if override else Path.home() / ".manas"


def config_path() -> Path:
    return home_dir() / "config.toml"


def default_database_path() -> Path:
    return home_dir() / "manas.db"


def legacy_home_dir() -> Path:
    return Path.home() / ".crowdforge"


def legacy_data_available() -> bool:
    if os.environ.get("MANAS_HOME"):
        return False
    legacy = legacy_home_dir()
    return not home_dir().exists() and legacy.exists() and any((legacy / name).exists() for name in ("config.toml", "crowdforge.db"))


def migrate_legacy_data() -> list[Path]:
    """Copy development data into MANAS, preserving the old directory untouched."""
    source = legacy_home_dir()
    destination = home_dir()
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    mappings = (("config.toml", "config.toml"), ("crowdforge.db", "manas.db"))
    for old_name, new_name in mappings:
        old_path, new_path = source / old_name, destination / new_name
        if old_path.exists() and not new_path.exists():
            shutil.copy2(old_path, new_path)
            copied.append(new_path)
    return copied


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    import tomllib
    return AppConfig.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))


def save_config(config: AppConfig) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"default_population_size = {config.default_population_size}", f'default_region = "{config.default_region}"',
        f'reasoning_engine = "{config.reasoning_engine}"', f"default_seed = {config.default_seed}",
        f'storage_path = {json.dumps(config.storage_path)}',
        f'model_paths = {json.dumps(config.model_paths)}',
        f'active_model_path = {json.dumps(config.active_model_path)}',
        f"color = {str(config.color).lower()}", f'log_level = "{config.log_level}"', "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

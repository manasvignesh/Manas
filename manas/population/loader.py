from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from manas.population.distributions import INDIA_V1


def _manifest() -> dict:
    packaged = files("manas").joinpath("data/populations/india/manifest.json")
    if packaged.is_file():
        return json.loads(packaged.read_text(encoding="utf-8"))
    source = Path(__file__).resolve().parents[2] / "data" / "populations" / "india" / "manifest.json"
    return json.loads(source.read_text(encoding="utf-8"))


def load_pack(name: str) -> dict:
    if name != "india_v1":
        raise ValueError(f"Unknown population pack: {name}")
    return {**INDIA_V1, "metadata": _manifest()}


def available_packs() -> list[dict]:
    return [_manifest()]

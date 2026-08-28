from __future__ import annotations

import json
from importlib.resources import files

from pydantic import BaseModel, Field


class ModelCatalogEntry(BaseModel):
    id: str
    display_name: str
    provider: str
    parameters: str
    quantization: str
    download_url: str
    size_bytes: int = Field(gt=0)
    sha256: str = Field(min_length=64, max_length=64)
    minimum_ram_gb: int
    recommended_ram_gb: int
    license: str
    description: str


def load_catalog() -> list[ModelCatalogEntry]:
    content = files("manas.models").joinpath("catalog.json").read_text(encoding="utf-8")
    return [ModelCatalogEntry.model_validate(item) for item in json.loads(content)]


def recommend(entries: list[ModelCatalogEntry], ram_bytes: int | None) -> ModelCatalogEntry:
    ram_gb = (ram_bytes or 0) / 1024 ** 3
    fitting = [entry for entry in entries if entry.minimum_ram_gb <= ram_gb]
    return max(fitting or entries, key=lambda entry: entry.recommended_ram_gb if entry in fitting else -entry.minimum_ram_gb)

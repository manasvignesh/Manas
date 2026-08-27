from __future__ import annotations

from manas.population.distributions import INDIA_V1


def load_pack(name: str) -> dict:
    if name != "india_v1":
        raise ValueError(f"Unknown population pack: {name}")
    return INDIA_V1


def available_packs() -> list[dict]:
    return [INDIA_V1["metadata"]]

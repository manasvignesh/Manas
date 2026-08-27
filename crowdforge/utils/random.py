from __future__ import annotations

import hashlib
import random


def seeded(seed: int, namespace: str = "") -> random.Random:
    """Return a stable namespaced random generator."""
    digest = hashlib.sha256(f"{seed}:{namespace}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


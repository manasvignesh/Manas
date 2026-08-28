from __future__ import annotations

import hashlib
import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

from manas.models.catalog import ModelCatalogEntry
from manas.utils.config import home_dir


class ChecksumError(RuntimeError):
    pass


def download_model(entry: ModelCatalogEntry, destination_dir: Path | None = None,
                   progress: Callable[[int, int], None] | None = None, opener=urllib.request.urlopen) -> Path:
    directory = destination_dir or home_dir() / "models"
    directory.mkdir(parents=True, exist_ok=True)
    final = directory / f"{entry.id}.gguf"
    partial = directory / f".{entry.id}.gguf.part"
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(entry.download_url, headers={"Range": f"bytes={offset}-"} if offset else {})
    response = opener(request, timeout=30)
    status = getattr(response, "status", 200)
    if offset and status != 206:
        offset = 0
    mode = "ab" if offset else "wb"
    received = offset
    with response, partial.open(mode) as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk: break
            handle.write(chunk); received += len(chunk)
            if progress: progress(received, entry.size_bytes)
        handle.flush(); os.fsync(handle.fileno())
    digest = hashlib.sha256()
    with partial.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    if digest.hexdigest().casefold() != entry.sha256.casefold():
        raise ChecksumError(f"Checksum validation failed for {entry.display_name}; the temporary file was preserved for diagnosis.")
    partial.replace(final)
    return final

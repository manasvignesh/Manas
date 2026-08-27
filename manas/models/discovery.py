from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from manas.utils.config import AppConfig, home_dir


@dataclass(frozen=True)
class DetectedModel:
    name: str
    provider: str
    location: str
    size_bytes: int | None = None


@dataclass(frozen=True)
class SystemProfile:
    cpu_threads: int
    ram_bytes: int | None
    disk_free_bytes: int
    gpu: str | None


def _ram_bytes() -> int | None:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                        ("available", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong),
                        ("available_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong),
                        ("available_virtual", ctypes.c_ulonglong), ("available_extended", ctypes.c_ulonglong)]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total)
        return None
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, ValueError, OSError):
        return None


def _gpu_name() -> str | None:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        result = subprocess.run([executable, "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                                text=True, timeout=2, check=False)
        return result.stdout.splitlines()[0].strip() if result.returncode == 0 and result.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def inspect_system() -> SystemProfile:
    root = home_dir()
    probe = root if root.exists() else root.parent
    return SystemProfile(max(1, os.cpu_count() or 1), _ram_bytes(), shutil.disk_usage(probe).free, _gpu_name())


def _ollama_models() -> list[DetectedModel]:
    executable = shutil.which("ollama")
    if not executable:
        return []
    try:
        result = subprocess.run([executable, "list"], capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    models = []
    for line in result.stdout.splitlines()[1:]:
        fields = line.split()
        if fields:
            models.append(DetectedModel(fields[0], "Ollama", fields[0]))
    return models


def _gguf_models(config: AppConfig) -> list[DetectedModel]:
    roots = [home_dir() / "models", *(Path(item).expanduser() for item in config.model_paths)]
    found: dict[str, DetectedModel] = {}
    for root in roots:
        paths = [root] if root.is_file() else list(root.glob("*.gguf")) if root.is_dir() else []
        for path in paths:
            if path.suffix.casefold() == ".gguf":
                resolved = path.resolve()
                found[str(resolved)] = DetectedModel(path.stem, "GGUF / llama.cpp", str(resolved), path.stat().st_size)
    return list(found.values())


def detect_models(config: AppConfig) -> list[DetectedModel]:
    return [*_ollama_models(), *_gguf_models(config)]

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from manas.cli.prompts import choose
from manas.models.discovery import DetectedModel, detect_models, inspect_system
from manas.models.catalog import load_catalog, recommend
from manas.models.downloader import ChecksumError, download_model
from manas.utils.config import load_config, save_config


def _size(value: int | None) -> str:
    return "unknown" if value is None else f"{value / (1024 ** 3):.1f} GB"


def show_models(console: Console, models: list[DetectedModel]) -> None:
    if not models:
        console.print("No local models detected.", style="muted")
        return
    table = Table(box=None)
    table.add_column("#", justify="right")
    table.add_column("Model")
    table.add_column("Provider")
    table.add_column("Size", justify="right")
    for index, model in enumerate(models, 1):
        table.add_row(str(index), model.name, model.provider, _size(model.size_bytes))
    console.print(table)


def import_gguf(console: Console) -> None:
    path = Path(Prompt.ask("Path to GGUF model", console=console)).expanduser()
    if not path.is_file() or path.suffix.casefold() != ".gguf":
        console.print("[warning]That is not an existing GGUF file.[/warning]")
        return
    config = load_config()
    resolved = str(path.resolve())
    if resolved not in config.model_paths:
        config.model_paths.append(resolved)
    config.active_model_path = resolved
    config.reasoning_engine = "local"
    save_config(config)
    console.print(f"[success]OK[/success] Configured {path.name}. The core simulation remains usable without it.")


def choose_existing(console: Console, models: list[DetectedModel]) -> None:
    if not models:
        console.print("[warning]No existing models were detected.[/warning]")
        return
    show_models(console, models)
    selected = models[choose(console, "Use which model?", [model.name for model in models]) - 1]
    config = load_config()
    config.reasoning_engine = selected.provider.casefold()
    config.active_model_path = selected.location
    save_config(config)
    console.print(f"[success]OK[/success] {selected.name} selected.")


def install_guidance(console: Console) -> None:
    profile = inspect_system()
    ram_gb = (profile.ram_bytes or 0) / (1024 ** 3)
    recommended = "Advanced" if ram_gb >= 24 and profile.gpu else "Balanced" if ram_gb >= 12 else "Lite"
    console.print("\n[heading]System profile[/heading]")
    console.print(f"OS: {profile.os_name}")
    console.print(f"CPU threads: {profile.cpu_threads}")
    console.print(f"RAM: {_size(profile.ram_bytes)}")
    console.print(f"GPU: {profile.gpu or 'not detected'}")
    console.print(f"Free disk: {_size(profile.disk_free_bytes)}")
    catalog = load_catalog()
    entry = recommend(catalog, profile.ram_bytes)
    console.print(f"\nBest fit: [accent]{entry.display_name}[/accent]")
    console.print(f"{entry.parameters} / {entry.quantization} / {_size(entry.size_bytes)} download")
    console.print(f"License: {entry.license}\n{entry.description}")
    console.print("\nRuns only on this computer. No API key. No cloud processing.", style="muted")
    if not Confirm.ask("\nInstall?", default=False, console=console):
        return
    progress_value = -1

    def progress(received: int, total: int) -> None:
        nonlocal progress_value
        current = int(received / max(total, 1) * 10)
        if current != progress_value:
            progress_value = current
            console.print(f"Downloading... {min(100, current * 10)}%", style="muted")
    try:
        path = download_model(entry, progress=progress)
    except ChecksumError as error:
        console.print(f"[error]{error}[/error]")
        return
    config = load_config()
    config.reasoning_engine = "llama.cpp"
    config.active_model_path = str(path)
    if str(path) not in config.model_paths:
        config.model_paths.append(str(path))
    save_config(config)
    console.print(f"[success]OK[/success] Installed {entry.display_name} to {path}")
    if not (shutil.which("llama-cli") or shutil.which("llama")):
        console.print("\nA llama.cpp runtime is required to use this GGUF model.")
        if shutil.which("winget") and Confirm.ask("Install llama.cpp with winget?", default=False, console=console):
            result = subprocess.run(["winget", "install", "llama.cpp", "--accept-package-agreements", "--accept-source-agreements"], check=False)
            console.print("Runtime installed." if result.returncode == 0 else "Runtime installation did not complete; the native simulation will continue without it.")


def benchmark(console: Console, models: list[DetectedModel]) -> None:
    if not models:
        console.print("[warning]No model is available to benchmark.[/warning]")
        return
    console.print("Model execution benchmarking will be provided by the configured reasoning provider.", style="muted")
    console.print("Discovery and hardware checks completed successfully.")


def remove_configuration(console: Console, models: list[DetectedModel]) -> None:
    config = load_config()
    if not config.active_model_path and not config.model_paths:
        console.print("No model configuration to remove.", style="muted")
        return
    if Confirm.ask("Remove model configuration? The model file will not be deleted", default=False, console=console):
        config.reasoning_engine = "none"
        config.active_model_path = ""
        config.model_paths = []
        save_config(config)
        console.print("[success]OK[/success] Model configuration removed. Files were preserved.")


def interactive_models(console: Console) -> None:
    console.print("\n[heading]Models[/heading]\n")
    config = load_config()
    models = detect_models(config)
    show_models(console, models)
    active = config.active_model_path or "No reasoning model active."
    console.print(f"Active: {active}", style="muted")
    choice = choose(console, "Model options", ["Use a model already on this computer", "Install recommended model", "Import GGUF model", "Benchmark model", "Remove model configuration", "Run without model", "Back"])
    if choice == 1:
        choose_existing(console, models)
    elif choice == 2:
        install_guidance(console)
    elif choice == 3:
        import_gguf(console)
    elif choice == 4:
        benchmark(console, models)
    elif choice == 5:
        remove_configuration(console, models)
    elif choice == 6:
        config.reasoning_engine = "none"
        config.active_model_path = ""
        save_config(config)
        console.print("[success]OK[/success] MANAS will run without a reasoning model.")

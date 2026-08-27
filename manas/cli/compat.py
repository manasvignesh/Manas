"""Short-lived compatibility entry point for the former project name."""

from rich.console import Console


def legacy_command() -> None:
    Console().print("CrowdForge has been renamed to [bold]MANAS[/bold].\n\nUse:\n  manas")

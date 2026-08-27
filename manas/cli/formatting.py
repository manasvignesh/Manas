"""Restrained terminal styling shared by all MANAS commands."""

from rich.console import Console
from rich.theme import Theme


THEME = Theme(
    {
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "dim",
        "accent": "cyan",
        "heading": "bold",
    }
)

console = Console(theme=THEME, highlight=False)


def money(value: float, pricing_model: str = "") -> str:
    if value <= 0:
        return "Free"
    suffix = {"monthly": "/month", "annual": "/year"}.get(pricing_model, "")
    return f"INR {value:g}{suffix}"


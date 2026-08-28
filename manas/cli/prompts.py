"""Keyboard-friendly conversational setup flows."""

from __future__ import annotations

from dataclasses import dataclass
import re
import secrets

from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt

from manas.simulation.models import ProductScenario, SimulationConfig
from manas.scenarios import parse_scenario


PRICING_MODELS = {1: "free", 2: "one-time", 3: "monthly", 4: "annual", 5: "custom"}


@dataclass(frozen=True)
class SimulationSetup:
    scenario: ProductScenario
    config: SimulationConfig


def choose(console: Console, title: str, options: list[str], default: int | None = None) -> int:
    console.print(f"\n[heading]{title}[/heading]\n")
    for index, option in enumerate(options, 1):
        console.print(f"  {index}. {option}")
    while True:
        value = IntPrompt.ask("\n>", default=default, console=console)
        if 1 <= value <= len(options):
            return value
        console.print(f"[warning]Choose a number from 1 to {len(options)}.[/warning]")


def ask_new_simulation(console: Console, default_population: int = 100, default_seed: int = 42) -> SimulationSetup | None:
    console.print("\n[heading]New simulation[/heading]")
    idea = Prompt.ask("\nWhat do you want to test?\n\n>", console=console).strip()
    if not idea:
        console.print("[warning]An idea is required.[/warning]")
        return None
    price = FloatPrompt.ask("\nPrice?\n\n>", default=0, console=console)
    pricing_choice = choose(console, "Pricing model?", ["Free", "One-time", "Monthly", "Annual", "Custom"], default=2)
    pricing_model = PRICING_MODELS[pricing_choice]
    if pricing_model == "free":
        price = 0
    elif pricing_model == "custom":
        pricing_model = Prompt.ask("Custom pricing model", console=console).strip() or "custom"
    population = IntPrompt.ask("\nPopulation?", default=default_population, console=console)
    choose(console, "Region?", ["India"], default=1)
    days = IntPrompt.ask("\nSimulation length in days?", default=30, console=console)
    seed = IntPrompt.ask("\nRandom seed?", default=default_seed, console=console)
    scenario = parse_scenario(idea, price=max(0, price), pricing_model=pricing_model, target_audience="Indian consumers")
    config = SimulationConfig(population_size=max(1, population), days=max(1, days), seed=seed)
    return SimulationSetup(scenario, config)


def ask_idea_first(console: Console, idea: str, default_population: int = 100) -> SimulationSetup | None:
    try:
        scenario = parse_scenario(idea)
    except ValueError as error:
        console.print(f"[warning]{error}[/warning]")
        return None
    if scenario.price > 0:
        if not Confirm.ask(f"\nI found {scenario.price:g} {scenario.pricing_model} pricing. Use that?", default=True, console=console):
            scenario.price = FloatPrompt.ask("Price", default=scenario.price, console=console)
    elif "free" not in idea.casefold():
        kind = choose(console, "I couldn't find a price. Is this:", ["Free", "Paid", "Price is not relevant"], default=3)
        if kind == 1:
            scenario.price, scenario.pricing_model = 0, "free"
        elif kind == 2:
            scenario.price = FloatPrompt.ask("Price", console=console)
            scenario.pricing_model = PRICING_MODELS[choose(console, "Pricing model?", ["Free", "One-time", "Monthly", "Annual", "Custom"], default=2)]
    return SimulationSetup(scenario, SimulationConfig(population_size=default_population, days=14, seed=secrets.randbelow(2_147_483_647)))


def parse_replay_change(text: str) -> tuple[str, str] | None:
    value = text.strip()
    patterns = [
        ("price", r"(?:set\s+)?price\s+(?:to|at|=)?\s*₹?\s*([\d,.]+)"),
        ("days", r"(?:run\s+for|duration\s+(?:to|=)?|days\s+(?:to|=)?)\s*(\d+)"),
        ("feature", r"(?:add\s+)?feature\s+(?:to|=)?\s*(.+)"),
        ("target", r"(?:target|audience)\s+(?:to|=)?\s*(.+)"),
        ("description", r"description\s+(?:to|=)?\s*(.+)"),
    ]
    for key, pattern in patterns:
        match = re.fullmatch(pattern, value, re.I)
        if match:
            return key, match.group(1).replace(",", "").strip()
    return None


def confirm_start(console: Console) -> bool:
    return Confirm.ask("\nStart simulation?", default=True, console=console)


def ask_replay_change(console: Console) -> tuple[str, str] | None:
    choice = choose(console, "What would you like to change?", ["Price", "Product description", "Feature", "Target audience", "Duration", "Cancel"])
    if choice == 6:
        return None
    keys = {1: "price", 2: "description", 3: "feature", 4: "target", 5: "days"}
    return keys[choice], Prompt.ask("\nNew value\n\n>", console=console)

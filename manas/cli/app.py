from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.prompt import Confirm, Prompt
from rich.table import Table

from manas import __version__
from manas.analytics.export import export_result
from manas.calibration import run_benchmarks
from manas.cli.formatting import console
from manas.cli.presenters import ProgressPresenter, show_agents, show_comparison, show_debug, show_header, show_ready, show_summary
from manas.cli.prompts import SimulationSetup, ask_idea_first, ask_new_simulation, ask_replay_change, choose, confirm_start, parse_replay_change
from manas.simulation.engine import SimulationEngine, SimulationResult
from manas.simulation.models import ProductScenario, SimulationConfig
from manas.scenarios import parse_scenario
from manas.reasoning.factory import build_reasoning_engine
from manas.storage import Database, SimulationRepository
from manas.utils.config import (
    AppConfig,
    default_database_path,
    home_dir,
    legacy_data_available,
    legacy_home_dir,
    load_config,
    migrate_legacy_data,
    save_config,
)


app = typer.Typer(no_args_is_help=False, help="MANAS - Many Agents, Networked Adaptive Society.", rich_markup_mode="rich")


def repository() -> SimulationRepository:
    config = load_config()
    path = Path(config.storage_path).expanduser() if config.storage_path else default_database_path()
    return SimulationRepository(Database(path))


def load_run(run_id: str, debug: bool = False) -> SimulationResult:
    try:
        repo = repository()
        return repo.load(repo.resolve_run_id(run_id))
    except Exception as error:
        if debug:
            raise
        console.print(f"[error]Could not load simulation {run_id!r}.[/error]")
        console.print("\nRun:\n  manas info\n\nto see whether local simulations are available.", style="muted")
        raise typer.Exit(1) from error


def execute_simulation(setup: SimulationSetup) -> SimulationResult:
    presenter = ProgressPresenter(console)
    presenter.started(setup.config.population_size)
    try:
        engine = SimulationEngine(reasoning=build_reasoning_engine(load_config()))
        result = asyncio.run(
            engine.run(setup.scenario, setup.config, day_observer=presenter.report)
        )
    except KeyboardInterrupt as error:
        console.print("\n[warning]Simulation stopped safely. No partial run was saved.[/warning]")
        raise typer.Exit(130) from error
    repository().save(result)
    show_summary(console, result)
    if setup.config.debug:
        show_debug(console, result)
    return result


def interactive_new(initial_idea: str | None = None) -> SimulationResult | None:
    config = load_config()
    if initial_idea is None:
        initial_idea = Prompt.ask("\nWhat do you want 100 minds to react to?\n\n>", console=console)
    setup = ask_idea_first(console, initial_idea, config.default_population_size)
    if setup is None:
        return None
    console.print(f"\nI'll introduce this to {setup.config.population_size} synthetic people across India\nand let the idea spread for {setup.config.days} simulated days.")
    return execute_simulation(setup) if Confirm.ask("\nStart?", default=True, console=console) else None


def interactive_post_run(result: SimulationResult) -> None:
    change = Prompt.ask("\nWhat would you change? (press Enter to finish)", default="", console=console)
    if change:
        parsed = parse_replay_change(change)
        if parsed:
            key, value = parsed
            replayed = run_replay(result, **{key: float(value) if key == "price" else value})
            if Confirm.ask("\nCompare this with the original?", default=True, console=console): show_comparison(console, result, replayed)
        else:
            console.print("I couldn't understand that change. Try 'price to 199', 'add feature student discount', or use manas replay latest.", style="warning")
    console.print("\nTry /runs, manas agents latest, or manas export latest when you want to explore further.", style="muted")


def interactive_home() -> None:
    show_header(console)
    while True:
        idea = Prompt.ask("\nWhat do you want to explore?\n\n>", console=console).strip()
        if idea in {"/exit", "/quit"}: return
        if idea == "/runs": show_runs()
        elif idea == "/models":
            from manas.models.manager import interactive_models
            interactive_models(console)
        elif idea == "/settings": show_settings()
        elif idea == "/help": console.print("/runs  /models  /settings  /help  /exit\nOr type any idea to start a society.")
        elif idea:
            result = interactive_new(idea)
            if result: interactive_post_run(result)


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Start a conversational session when no command is supplied."""
    if ctx.invoked_subcommand is None:
        try:
            interactive_home()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[muted]Session ended.[/muted]")


@app.command("init")
def initialize(force: bool = typer.Option(False, help="Replace the existing configuration with defaults.")) -> None:
    """Create local configuration and storage."""
    show_header(console)
    console.print("\n[heading]MANAS setup[/heading]\n")
    if legacy_data_available():
        console.print(f"Existing CrowdForge development data found at {legacy_home_dir()}.")
        if Confirm.ask("Migrate a copy to MANAS?", default=True, console=console):
            copied = migrate_legacy_data()
            console.print(f"[success]OK[/success] Copied {len(copied)} data file(s). The original data was preserved.")
    path = home_dir() / "config.toml"
    if path.exists() and not force:
        console.print(f"[success]OK[/success] Configuration ({path})")
    else:
        save_config(AppConfig())
        console.print("[success]OK[/success] Configuration")
    Database(default_database_path()).initialize()
    console.print("[success]OK[/success] Database")
    console.print("[success]OK[/success] India V1 population pack")
    (home_dir() / "models").mkdir(parents=True, exist_ok=True)
    console.print("\n[heading]Reasoning model[/heading]\nNo model configured.")
    console.print("\nYou can add one later with:\n  manas models")
    console.print("\n[success]MANAS is ready.[/success]")


@app.command()
def simulate(
    idea: Annotated[str | None, typer.Option(help="Product, policy, service, or startup idea.")] = None,
    population: int = typer.Option(100, min=1, max=10_000),
    days: int = typer.Option(30, min=1, max=365),
    seed: int = typer.Option(42),
    price: float | None = typer.Option(None, min=0),
    pricing_model: str | None = typer.Option(None),
    target: str | None = typer.Option(None),
    description: str = typer.Option(""),
    debug: bool = typer.Option(False),
) -> None:
    """Run a simulation interactively or entirely from flags."""
    if idea is None:
        result = interactive_new()
        if result:
            interactive_post_run(result)
        return
    try:
        scenario = parse_scenario(idea, description=description or None, target_audience=target, price=price, pricing_model=pricing_model)
    except ValueError as error:
        console.print(f"[error]{error}[/error]")
        raise typer.Exit(2) from error
    execute_simulation(SimulationSetup(scenario, SimulationConfig(population_size=population, days=days, seed=seed, debug=debug)))


def replay_interactive(original: SimulationResult) -> SimulationResult | None:
    natural = Prompt.ask("What would you change?", console=console)
    change = parse_replay_change(natural) or ask_replay_change(console)
    if change is None:
        return None
    key, value = change
    kwargs = {key: value}
    if key == "price":
        kwargs[key] = float(value)
    return run_replay(original, **kwargs)


def run_replay(original: SimulationResult, price: float | None = None, description: str | None = None,
               feature: str | None = None, target: str | None = None, days: int | str | None = None,
               seed: int | None = None, debug: bool = False) -> SimulationResult:
    scenario_updates = {}
    if price is not None:
        scenario_updates["price"] = price
    if description is not None:
        scenario_updates["description"] = description
    if target is not None:
        scenario_updates["target_audience"] = target
    if feature:
        scenario_updates["features"] = [*original.scenario.features, feature]
    config_updates = {"debug": debug}
    if days is not None:
        config_updates["days"] = int(days)
    if seed is not None:
        config_updates["seed"] = seed
    return execute_simulation(SimulationSetup(original.scenario.model_copy(update=scenario_updates), original.config.model_copy(update=config_updates)))


@app.command()
def replay(
    run_id: str,
    price: float | None = typer.Option(None),
    description: str | None = typer.Option(None),
    feature: str | None = typer.Option(None),
    target: str | None = typer.Option(None),
    days: int | None = typer.Option(None, min=1),
    seed: int | None = typer.Option(None),
    debug: bool = typer.Option(False),
) -> None:
    """Replay the same seeded society with controlled scenario changes."""
    original = load_run(run_id, debug)
    if all(value is None for value in (price, description, feature, target, days, seed)):
        replay_interactive(original)
    else:
        run_replay(original, price, description, feature, target, days, seed, debug)


@app.command()
def compare(run_a: str, run_b: str, debug: bool = typer.Option(False)) -> None:
    """Compare two saved simulated worlds."""
    show_comparison(console, load_run(run_a, debug), load_run(run_b, debug))


@app.command()
def agents(run_id: str, search: str = typer.Option("", help="Name, ID, city, or occupation."), limit: int = typer.Option(20, min=1), debug: bool = typer.Option(False)) -> None:
    """Explore persistent agents and their decision explanations."""
    show_agents(console, load_run(run_id, debug), search, limit)


@app.command("export")
def export_command(run_id: str, output: Path = typer.Option(Path("exports")), formats: str = typer.Option("json,csv,markdown"), debug: bool = typer.Option(False)) -> None:
    """Export profiles, events, state, and insights."""
    result = load_run(run_id, debug)
    paths = export_result(result, output, {item.strip().lower() for item in formats.split(",")})
    for path in paths:
        console.print(f"[success]OK[/success] {path.resolve()}")


def show_settings() -> None:
    config = load_config()
    table = Table(title="Settings", box=None, show_header=False)
    for key, value in config.model_dump().items():
        table.add_row(key.replace("_", " ").title(), str(value or "default"))
    console.print(table)
    console.print(f"\n{home_dir() / 'config.toml'}", style="muted")


@app.command()
def settings() -> None:
    """Show active local settings."""
    show_settings()


@app.command()
def models() -> None:
    """Discover and manage optional local reasoning models."""
    from manas.models.manager import interactive_models
    interactive_models(console)


@app.command()
def benchmark() -> None:
    """Run behavioral sanity checks (not empirical calibration)."""
    console.print("\n[heading]MANAS behavior benchmarks[/heading]\n")
    results = run_benchmarks()
    for result in results:
        status = "[success]PASS[/success]" if result.passed else "[error]FAIL[/error]"
        console.print(f"{status} {result.name}")
        console.print(f"     {result.evidence}", style="muted")
    console.print("\nThese are model invariants, not evidence that MANAS predicts real populations.", style="muted")
    if not all(result.passed for result in results):
        raise typer.Exit(1)


@app.command()
def info() -> None:
    """Show version, storage location, and saved-run count."""
    show_header(console)
    runs = repository().list_runs()
    console.print(f"\nVersion {__version__}")
    console.print(f"Stored runs: {len(runs)}")
    console.print(f"Data: {default_database_path()}")
    console.print("Reasoning: optional and disabled by default")


def show_runs() -> None:
    records = repository().list_run_records()
    if not records:
        console.print("No saved simulations yet.", style="muted"); return
    console.print("\n[heading]Runs[/heading]\n")
    for index, record in enumerate(records, 1):
        pin = " (pinned)" if record.pinned else ""
        replay = " replay" if index > 1 and record.scenario_name == records[index - 2].scenario_name else ""
        console.print(f"{index:>2}  {record.scenario_name[:38]}{replay}{pin}")
        console.print(f"    {record.population_size} people / {record.days} days / {record.run_id}", style="muted")


@app.command()
def runs(pin: str | None = typer.Option(None, help="Pin a run by number, alias, or ID."), unpin: str | None = typer.Option(None)) -> None:
    """List saved simulations with readable aliases."""
    repo = repository()
    if pin: console.print(f"Pinned {repo.pin(pin)}", style="success")
    if unpin: console.print(f"Unpinned {repo.pin(unpin, False)}", style="success")
    show_runs()

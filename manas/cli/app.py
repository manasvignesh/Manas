from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from manas import __version__
from manas.analytics.export import export_result
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import ProductScenario, SimulationConfig
from manas.storage import Database, SimulationRepository
from manas.utils.config import AppConfig, default_database_path, home_dir, load_config, save_config

app = typer.Typer(no_args_is_help=False, help="MANAS - synthetic society simulator.")
console = Console()


def repository() -> SimulationRepository:
    config = load_config()
    return SimulationRepository(Database(Path(config.storage_path).expanduser() if config.storage_path else default_database_path()))


def show_summary(result) -> None:
    summary = result.summary
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("Synthetic people", str(summary.population_size))
    table.add_row("Simulated days", str(summary.days))
    table.add_row("Social interactions", str(summary.interactions))
    table.add_row("Significant opinion changes", str(summary.opinion_changes))
    table.add_row("Average purchase intent", f"{summary.average_purchase_intent:.1%}")
    console.print(Panel(table, title=f"[bold]Simulation complete - {summary.run_id}[/bold]", border_style="cyan"))
    for item in summary.insights:
        console.print(f"  - {item}")
    console.print(f"\n[dim]{summary.disclaimer}[/dim]")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Launch the TUI when no command is supplied."""
    if ctx.invoked_subcommand is None:
        from manas.cli.tui import MANASApp
        MANASApp().run()


@app.command("init")
def initialize(force: bool = typer.Option(False, help="Replace the existing config with defaults.")) -> None:
    """Create local configuration and storage."""
    path = home_dir() / "config.toml"
    if path.exists() and not force:
        console.print(f"[yellow]Already initialized:[/] {path}")
        return
    config_path = save_config(AppConfig())
    Database(default_database_path()).initialize()
    (home_dir() / "models").mkdir(parents=True, exist_ok=True)
    console.print(Panel.fit(f"[bold cyan]MANAS is ready.[/]\nConfig: {config_path}\nData: {default_database_path()}\n\nNo model or API key is required."))


@app.command()
def simulate(
    idea: Annotated[str, typer.Option(prompt=True, help="Product or startup idea.")] = "",
    population: int = typer.Option(100, min=1, max=10_000), days: int = typer.Option(30, min=1, max=365), seed: int = typer.Option(42),
    price: float = typer.Option(0, min=0), pricing_model: str = typer.Option("one-time"),
    target: str = typer.Option("general consumers"), description: str = typer.Option(""), debug: bool = typer.Option(False),
) -> None:
    """Run a new product-launch simulation."""
    scenario = ProductScenario(name=idea, description=description or idea, target_audience=target, price=price, pricing_model=pricing_model,
                               category=idea, concerns=["price", "privacy"])
    config = SimulationConfig(population_size=population, days=days, seed=seed, debug=debug)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True, console=console) as progress:
        task = progress.add_task("Creating synthetic society...", total=None)
        def update(day: int, total: int, message: str) -> None:
            progress.update(task, description=f"Simulating day {day}/{total} - {message}")
        result = asyncio.run(SimulationEngine().run(scenario, config, update))
    repository().save(result)
    console.print("[green]OK[/] agents generated  [green]OK[/] social graph created  [green]OK[/] opinions evolved")
    show_summary(result)
    if debug and result.decisions:
        decision = result.decisions[-1]
        console.print(Panel("\n".join(decision.explanation) + f"\n\n{decision.probabilities}", title=f"Debug - {decision.agent_id}"))


@app.command()
def replay(run_id: str, price: float | None = typer.Option(None), seed: int | None = typer.Option(None)) -> None:
    """Replay a saved population, optionally changing scenario variables."""
    original = repository().load(run_id)
    scenario = original.scenario.model_copy(update={"price": price}) if price is not None else original.scenario.model_copy()
    config = original.config.model_copy(update={"seed": seed if seed is not None else original.config.seed})
    # The population generator is seeded, so regenerating restores the exact pre-run society state.
    result = asyncio.run(SimulationEngine().run(scenario, config))
    repository().save(result)
    show_summary(result)


@app.command()
def compare(run_a: str, run_b: str) -> None:
    """Compare two saved worlds."""
    left, right = repository().load(run_a), repository().load(run_b)
    table = Table(title="Controlled world comparison")
    table.add_column("Metric"); table.add_column(f"World A - INR {left.scenario.price:g}", justify="right"); table.add_column(f"World B - INR {right.scenario.price:g}", justify="right")
    table.add_row("Purchase intent", f"{left.summary.average_purchase_intent:.1%}", f"{right.summary.average_purchase_intent:.1%}")
    table.add_row("Positive", f"{left.summary.sentiment['positive']:.1%}", f"{right.summary.sentiment['positive']:.1%}")
    table.add_row("Negative", f"{left.summary.sentiment['negative']:.1%}", f"{right.summary.sentiment['negative']:.1%}")
    console.print(table); console.print(f"[dim]{left.summary.disclaimer}[/dim]")


@app.command()
def agents(run_id: str, limit: int = typer.Option(20, min=1)) -> None:
    """Explore agents from a saved simulation."""
    result = repository().load(run_id)
    table = Table(title=f"Agents - {run_id}")
    for heading in ("ID", "Person", "Context", "Stance", "Intent"):
        table.add_column(heading)
    for agent in result.agents[:limit]:
        table.add_row(agent.id, agent.name, f"{agent.age} / {agent.location} / {agent.occupation}", agent.opinion.sentiment, f"{agent.opinion.purchase_intent:.0%}")
    console.print(table)


@app.command("export")
def export_command(run_id: str, output: Path = typer.Option(Path("exports")), formats: str = typer.Option("json,csv,markdown")) -> None:
    """Export simulation data and insights."""
    paths = export_result(repository().load(run_id), output, {f.strip().lower() for f in formats.split(",")})
    for path in paths:
        console.print(f"[green]OK[/] {path.resolve()}")


@app.command()
def settings() -> None:
    """Show active local settings."""
    config = load_config()
    console.print(Panel(config.model_dump_json(indent=2), title=str(home_dir() / "config.toml")))


@app.command()
def info() -> None:
    """Show version, paths, and available population packs."""
    runs = repository().list_runs()
    console.print(Panel.fit(f"[bold cyan]MANAS[/]\nSynthetic Society Simulator\n\nVersion {__version__}\nStored runs: {len(runs)}\nData: {default_database_path()}\nReasoning: optional (disabled by default)"))

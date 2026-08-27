"""Presentation policy for deciding what simulation information reaches users."""

from __future__ import annotations

from collections import Counter

from rich.console import Console
from rich.table import Table

from manas.agents.models import Agent
from manas.cli.formatting import money
from manas.simulation.engine import SimulationResult
from manas.simulation.models import DayReport, Decision, ProductScenario, SimulationConfig


DISCLAIMER = "These results describe this simulated population and are not equivalent to real-world survey statistics."


def show_header(console: Console) -> None:
    console.print("[heading]MANAS[/heading]")
    console.print("Many Agents, Networked Adaptive Society", style="muted")
    console.print("\n[accent]One idea. Many minds.[/accent]")


def show_ready(console: Console, scenario: ProductScenario, config: SimulationConfig) -> None:
    console.print("\n[success]Ready.[/success]\n")
    table = Table(show_header=False, box=None, padding=(0, 3))
    table.add_row("Idea", scenario.name)
    table.add_row("Price", money(scenario.price, scenario.pricing_model))
    table.add_row("Population", str(config.population_size))
    table.add_row("Region", "India")
    table.add_row("Duration", f"{config.days} days")
    table.add_row("Seed", str(config.seed))
    console.print(table)


class ProgressPresenter:
    """Filters daily callbacks down to useful milestones."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def started(self, population: int) -> None:
        self.console.print("\n[heading]Creating society...[/heading]\n")
        self.console.print(f"[success]OK[/success] {population} people generated")
        self.console.print("[success]OK[/success] relationships and communities created")
        self.console.print("[success]OK[/success] initial exposure seeded")
        self.console.print("\nSimulation started.")

    def update(self, day: int, total: int, message: str) -> None:
        if day == 1 or day == total or day % 5 == 0:
            self.console.print(f"\n[heading]Day {day:02d}[/heading]")
            self.console.print(message, style="muted")

    def report(self, report: DayReport) -> None:
        if report.day != 1 and report.day != report.total_days and report.day % 5:
            return
        self.console.print(f"\n[heading]Day {report.day:02d}[/heading]")
        if report.actions:
            action, count = max(report.actions.items(), key=lambda item: item[1])
            self.console.print(f"{report.reactions} reactions; {report.opinion_changes} significant opinion shifts.")
            self.console.print(f"Most common response: {action.replace('_', ' ')} ({count}).")
        else:
            self.console.print("No major reaction was triggered today.")
        self.console.print(f"{report.awareness} agents have encountered the idea.", style="muted")


def _notable_decisions(result: SimulationResult, limit: int = 3) -> list[tuple[Agent, Decision]]:
    agents = {agent.id: agent for agent in result.agents}
    eligible = [d for d in result.decisions if d.action in {"buy", "reject", "ask_friend"}]
    eligible.sort(key=lambda d: d.probabilities.get(d.action, 0), reverse=True)
    seen: set[str] = set()
    chosen = []
    for decision in eligible:
        if decision.agent_id not in seen:
            chosen.append((agents[decision.agent_id], decision))
            seen.add(decision.agent_id)
        if len(chosen) == limit:
            break
    return chosen


def show_activity(console: Console, result: SimulationResult) -> None:
    notable = _notable_decisions(result)
    if not notable:
        return
    console.print("\n[heading]Notable reactions[/heading]\n")
    descriptions = {
        "buy": "Interest overcame the remaining concerns.",
        "reject": "The idea did not clear this person's trust and value threshold.",
        "ask_friend": "Uncertainty led to a peer conversation.",
    }
    for agent, decision in notable:
        console.print(f"[accent]{agent.name}[/accent] / {agent.location}")
        console.print(descriptions[decision.action])
        console.print(f"Why: {decision.explanation[0]}; {decision.explanation[-1]}", style="muted")
        console.print()


def show_summary(console: Console, result: SimulationResult) -> None:
    summary = result.summary
    console.print("\n[heading]Simulation complete.[/heading]\n")
    console.print(f"Run {summary.run_id}", style="muted")
    console.print(f"{summary.population_size} synthetic people")
    console.print(f"{summary.days} simulated days")
    console.print(f"{summary.interactions} peer conversations")
    console.print(f"{summary.opinion_changes} significant opinion changes")
    console.print(f"{summary.average_purchase_intent:.0%} average purchase intent")
    console.print("\n[heading]Emerging signals[/heading]\n")
    for insight in summary.insights:
        console.print(f"- {insight}")
    show_activity(console, result)
    console.print(DISCLAIMER, style="muted")


def show_debug(console: Console, result: SimulationResult, count: int = 3) -> None:
    console.print("\n[heading]Developer details[/heading]")
    for decision in result.decisions[-count:]:
        console.print(f"\n[accent]{decision.agent_id} / day {decision.day} / {decision.action}[/accent]")
        console.print(f"probabilities: {decision.probabilities}")
        console.print(f"modifiers: {decision.factors}")


def show_agents(console: Console, result: SimulationResult, query: str = "", limit: int = 20) -> None:
    normalized = query.casefold().strip()
    matches = [a for a in result.agents if not normalized or normalized in f"{a.id} {a.name} {a.location} {a.occupation}".casefold()]
    if not matches:
        console.print("[warning]No matching agents.[/warning]")
        return
    for agent in matches[:limit]:
        show_agent(console, result, agent)


def show_agent(console: Console, result: SimulationResult, agent: Agent) -> None:
    console.print(f"\n[heading]{agent.name}[/heading]")
    console.print(f"{agent.age} / {agent.location} / {agent.occupation}", style="muted")
    console.print("\n[heading]Current stance[/heading]")
    console.print(f"{agent.opinion.sentiment.title()}, purchase intent {agent.opinion.purchase_intent:.0%}")
    console.print("\n[heading]Goals[/heading]")
    for goal in agent.goals:
        console.print(f"- {goal}")
    console.print("\n[heading]Relevant memories[/heading]")
    memories = agent.relevant_memories(result.config.days, 4)
    if memories:
        for memory in memories:
            console.print(f"- Day {memory.day}: {memory.content}")
    else:
        console.print("- No salient memories recorded", style="muted")
    decisions = [d for d in result.decisions if d.agent_id == agent.id]
    if decisions:
        console.print("\n[heading]Why?[/heading]")
        for factor in decisions[-1].explanation:
            console.print(factor)


def show_comparison(console: Console, left: SimulationResult, right: SimulationResult) -> None:
    console.print("\n[heading]Scenario comparison[/heading]\n")
    table = Table(box=None)
    table.add_column("")
    table.add_column("WORLD A", justify="right")
    table.add_column("WORLD B", justify="right")
    table.add_row("Price", money(left.scenario.price, left.scenario.pricing_model), money(right.scenario.price, right.scenario.pricing_model))
    table.add_row("Purchase intent", f"{left.summary.average_purchase_intent:.0%}", f"{right.summary.average_purchase_intent:.0%}")
    table.add_row("Positive sentiment", f"{left.summary.sentiment['positive']:.0%}", f"{right.summary.sentiment['positive']:.0%}")
    table.add_row("Negative sentiment", f"{left.summary.sentiment['negative']:.0%}", f"{right.summary.sentiment['negative']:.0%}")
    console.print(table)
    delta = right.summary.average_purchase_intent - left.summary.average_purchase_intent
    direction = "increased" if delta >= 0 else "decreased"
    console.print("\n[heading]Biggest change[/heading]")
    console.print(f"Purchase intent {direction} by {abs(delta):.0%} between these simulated worlds.")
    console.print(f"\n{DISCLAIMER}", style="muted")

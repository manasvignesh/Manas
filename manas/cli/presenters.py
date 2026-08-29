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
    console.print(table)


class ProgressPresenter:
    """Filters daily callbacks down to useful milestones."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._last_topics: tuple[str, ...] = ()

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
        topics_key = tuple(report.spreading_topics)
        if report.spreading_topics and topics_key != self._last_topics:
            topics = ", ".join(report.spreading_topics[:2])
            self.console.print(f"A conversation about {topics} is spreading through social circles.", style="warning")
            self._last_topics = topics_key


def _notable_decisions(result: SimulationResult, limit: int = 3) -> list[tuple[Agent, Decision]]:
    agents = {agent.id: agent for agent in result.agents}
    eligible = [d for d in result.decisions if d.action in {"buy_now", "subscribe", "reject", "ask_friend", "wait_for_discount", "search_reviews"}]
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


def reaction_narrative(agent: Agent, decision: Decision, scenario: ProductScenario) -> str:
    context = agent.life_contexts[0].description if agent.life_contexts else f"{agent.name} is balancing {agent.goals[0]} with everyday constraints."
    experience = agent.category_experiences.get(scenario.category)
    variants = {
        "subscribe": ["decided the ongoing support could justify a subscription", "saw enough personal value to consider paying monthly"],
        "buy_now": ["felt ready to pay now", "decided the benefit was worth acting on"],
        "reject": ["decided the unresolved concerns outweighed the promise", "could not find enough value or trust to continue"],
        "ask_friend": ["wanted a trusted person's view before going further", "turned to someone familiar for a reality check"],
        "wait_for_discount": ["remained interested but chose to wait for a better price", "could imagine using it, but not at the current price"],
        "search_reviews": ["looked for evidence from people who had actually tried it", "wanted proof of results before committing"],
    }
    choices = variants.get(decision.action, [f"chose to {decision.action.replace('_', ' ')}"])
    index = sum(ord(character) for character in agent.id) % len(choices)
    action_sentence = f"{agent.name} {choices[index]}."
    if decision.factors.get("money_conflict", 0) > .5:
        detail = "The price competes with immediate priorities, so relevance alone was not enough."
    elif experience and experience.products_used:
        detail = f"Past experience with {experience.products_used} {scenario.category} option(s) shaped what felt credible this time."
    elif decision.factors.get("target_match", 0) >= .65:
        detail = "The idea fits their current stage of life, making its promise unusually concrete."
    elif agent.memories and agent.memories[0].category not in {"decision", "general"}:
        detail = f"A recent memory about {agent.memories[0].category} was still part of the decision."
    else:
        detail = "Their current goals made the idea relevant, while trust still had to be earned."
    return f"{context} {action_sentence} {detail}"


def show_activity(console: Console, result: SimulationResult) -> None:
    notable = _notable_decisions(result)
    if not notable:
        return
    console.print("\n[heading]Notable reactions[/heading]\n")
    for agent, decision in notable:
        console.print(f"[accent]{agent.name}[/accent] / {agent.location}")
        console.print(reaction_narrative(agent, decision, result.scenario))
        console.print("What mattered:")
        for reason in decision.explanation[1:]:
            console.print(f"- {reason}")
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
    console.print("\n[heading]WHAT MANAS FOUND[/heading]\n")
    labels = {
        "who_wants_this": "Who wants this", "who_does_not": "Who does not", "strongest_pull": "Strongest pull",
        "biggest_resistance": "Biggest resistance", "unexpected": "Unexpected perspective", "social_effect": "Social effect",
    }
    for key, label in labels.items():
        if key in summary.findings:
            console.print(f"[heading]{label}[/heading]\n{summary.findings[key]}\n")
    show_activity(console, result)
    if result.cascades:
        cascade = result.cascades[0]
        communities = cascade.communities_touched or min(len(cascade.communities), cascade.reached)
        transmissions = cascade.transmission_count or max(0, cascade.reached - 1)
        message_kind = "concern" if cascade.stance == "negative" else "recommendation" if cascade.stance == "positive" else "discussion"
        community_word = "community" if communities == 1 else "communities"
        console.print("\n[heading]Social ripple[/heading]")
        console.print(f"A {cascade.topic} {message_kind} reached {cascade.reached} unique people across {communities} connected {community_word} through {transmissions} transmissions.")
    if result.communities:
        community = result.communities[0]
        console.print("\n[heading]Most active circle[/heading]")
        console.print(f"{community.name}: {community.size} people, {community.sentiment} response; most discussed: {community.most_discussed}.")
    console.print("\n[heading]What you should test with real people[/heading]")
    for recommendation in summary.real_world_tests:
        console.print(f"- {recommendation}")
    console.print(DISCLAIMER, style="muted")


def show_debug(console: Console, result: SimulationResult, count: int = 3) -> None:
    console.print("\n[heading]Developer details[/heading]")
    for decision in result.decisions[-count:]:
        console.print(f"\n[accent]{decision.agent_id} / day {decision.day} / {decision.action}[/accent]")
        console.print(f"probabilities: {decision.probabilities}")
        console.print(f"modifiers: {decision.factors}")


def show_agents(console: Console, result: SimulationResult, query: str = "", limit: int = 20,
                debug: bool = False) -> None:
    normalized = query.casefold().strip()
    matches = [a for a in result.agents if not normalized or normalized in f"{a.id} {a.name} {a.location} {a.occupation}".casefold()]
    if not matches:
        console.print("[warning]No matching agents.[/warning]")
        return
    for agent in matches[:limit]:
        show_agent(console, result, agent, debug)


def show_agent(console: Console, result: SimulationResult, agent: Agent, debug: bool = False) -> None:
    console.print(f"\n[heading]{agent.name}[/heading]")
    console.print(f"{agent.age} / {agent.location} / {agent.occupation}", style="muted")
    if agent.life_contexts:
        console.print("\n[heading]Right now[/heading]")
        console.print(agent.life_contexts[0].description)
    console.print("\n[heading]They care about[/heading]")
    for item in list(dict.fromkeys([*agent.interests, *agent.goals]))[:5]: console.print(f"- {item}")
    tendencies = []
    if agent.personality.frugality > .65: tendencies.append("careful with money and likely to compare alternatives")
    if agent.personality.skepticism > .65: tendencies.append("skeptical until there is credible evidence")
    if agent.personality.social_conformity > .65: tendencies.append("strongly influenced by trusted people")
    if agent.personality.impulsiveness > .7: tendencies.append("occasionally acts quickly when something connects to a hobby")
    console.print("\n[heading]Tendencies[/heading]")
    for item in tendencies or ["balances curiosity with familiar routines"]: console.print(f"- {item}")
    if agent.contradictions:
        console.print("\n[heading]Contradiction[/heading]")
        console.print(agent.contradictions[0])
    decisions = [d for d in result.decisions if d.agent_id == agent.id]
    console.print("\n[heading]Their story[/heading]")
    if decisions:
        for decision in decisions[-5:]:
            console.print(f"Day {decision.day}: {decision.explanation[0]} They chose to {decision.action.replace('_', ' ')}.")
    else:
        console.print("The idea did not reach them during this run.", style="muted")
    if decisions:
        console.print("\n[heading]Current decision[/heading]")
        console.print(f"Would {decisions[-1].action.replace('_', ' ')}.")
        console.print("\n[heading]What mattered[/heading]")
        for reason in decisions[-1].explanation[1:]: console.print(f"- {reason}")
    if debug:
        console.print("\n[heading]Developer trace[/heading]")
        if decisions:
            latest = decisions[-1]
            console.print(f"target relevance: {latest.factors.get('target_match', 0):.3f}")
            console.print(f"perception: {latest.perception}")
            console.print(f"motivations: {latest.motivations}")
            console.print(f"consideration set: {latest.consideration_set}")
            console.print(f"action distribution: {latest.probabilities}")
        relevant = agent.relevant_memories(result.config.days, topics={result.scenario.category, "price", "privacy"})
        console.print(f"memory influence: {[memory.content for memory in relevant]}")
        interactions = [item for item in (result.social_interactions or [])
                        if agent.id in {item.speaker_id, item.listener_id}]
        console.print(f"social influence: {[item.model_dump(mode='json') for item in interactions[-5:]]}")
        console.print(f"current state after transitions: {agent.state.model_dump(mode='json')}")


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
    pairs = [(a, b) for a in left.agents for b in right.agents if a.id == b.id]
    def price_pressure_change(agent_id: str) -> float | None:
        before = [d.factors.get("money_conflict", 0) for d in left.decisions if d.agent_id == agent_id]
        after = [d.factors.get("money_conflict", 0) for d in right.decisions if d.agent_id == agent_id]
        if not before or not after:
            return None
        return abs(sum(after) / len(after) - sum(before) / len(before))

    sensitive = [change for a, _ in pairs if a.price_sensitivity >= .65
                 and (change := price_pressure_change(a.id)) is not None]
    insensitive = [change for a, _ in pairs if a.price_sensitivity <= .35
                   and (change := price_pressure_change(a.id)) is not None]
    if sensitive:
        console.print(f"Price-sensitive people's perceived price pressure changed by {sum(sensitive)/len(sensitive):.0%} on average.")
    if insensitive:
        console.print(f"Price-insensitive people's perceived price pressure changed by {sum(insensitive)/len(insensitive):.0%} on average.")
    low_relevance = []
    for agent_a, agent_b in pairs:
        relevant = [d.factors.get("relevance", 0) for d in left.decisions if d.agent_id == agent_a.id]
        if relevant and sum(relevant)/len(relevant) < .25: low_relevance.append(agent_b.opinion.purchase_intent - agent_a.opinion.purchase_intent)
    if low_relevance:
        console.print(f"People with little category relevance moved only {sum(low_relevance)/len(low_relevance):.0%} on average.")
    console.print(f"\n{DISCLAIMER}", style="muted")

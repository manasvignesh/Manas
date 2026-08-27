from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from crowdforge.agents.models import Agent, Memory
from crowdforge.analytics.insights import analyze
from crowdforge.behavior.engine import BehaviorEngine
from crowdforge.population.generator import PopulationGenerator
from crowdforge.reasoning.base import NoOpReasoningEngine, ReasoningEngine
from crowdforge.simulation.models import Decision, ProductScenario, SimulationConfig, SimulationEvent, SimulationSummary
from crowdforge.simulation.scheduler import EventScheduler
from crowdforge.society.graph import SocietyGraph
from crowdforge.society.influence import influence_shift
from crowdforge.utils.random import clamp, seeded


@dataclass
class SimulationResult:
    run_id: str
    created_at: str
    scenario: ProductScenario
    config: SimulationConfig
    agents: list[Agent]
    graph: SocietyGraph
    events: list[SimulationEvent]
    decisions: list[Decision]
    summary: SimulationSummary


class SimulationEngine:
    def __init__(self, behavior: BehaviorEngine | None = None, reasoning: ReasoningEngine | None = None) -> None:
        self.behavior = behavior or BehaviorEngine()
        self.reasoning = reasoning or NoOpReasoningEngine()

    async def run(self, scenario: ProductScenario, config: SimulationConfig,
                  progress: Callable[[int, int, str], None] | None = None,
                  base_agents: list[Agent] | None = None) -> SimulationResult:
        rng = seeded(config.seed, "simulation")
        agents = [a.model_copy(deep=True) for a in base_agents] if base_agents else PopulationGenerator(config.seed, config.population_pack).generate(config.population_size)
        by_id = {agent.id: agent for agent in agents}
        society = SocietyGraph(config.seed)
        society.build(agents)
        scheduler = EventScheduler()
        events: list[SimulationEvent] = []
        decisions: list[Decision] = []
        opinion_changes = 0
        initial_count = max(1, int(len(agents) * .35))
        initial_targets = rng.sample(list(by_id), k=min(initial_count, len(agents)))
        scheduler.schedule(SimulationEvent(id="event_000001", day=1, event_type="product_seen", target_agent_ids=initial_targets, intensity=.65))
        sequence = 2
        for day in range(1, config.days + 1):
            # Organic media/review events reach a subset; idle agents are never evaluated.
            if day in {3, 7, 12, 18, 24} and day <= config.days:
                event_type = rng.choice(["ad_seen", "positive_review", "negative_review", "influencer_mention", "viral_discussion"])
                aware = [a.id for a in agents if a.opinion.awareness > .05]
                pool = aware or list(by_id)
                target_count = min(len(pool), max(1, int(len(agents) * rng.uniform(.08, .18))))
                scheduler.schedule(SimulationEvent(id=f"event_{sequence:06d}", day=day, event_type=event_type,
                    target_agent_ids=rng.sample(pool, target_count), intensity=rng.uniform(.35, .8),
                    sentiment=-.55 if "negative" in event_type else .5 if event_type in {"positive_review", "influencer_mention"} else .1))
                sequence += 1
            for event in scheduler.events_for_day(day):
                events.append(event)
                for agent_id in event.target_agent_ids:
                    agent = by_id.get(agent_id)
                    if agent is None:
                        continue
                    before = agent.opinion.purchase_intent
                    decision = self.behavior.evaluate(agent, scenario, event, rng)
                    decisions.append(decision)
                    await self.reasoning.reason(agent, event, {"scenario": scenario, "decision": decision})
                    self._update_agent(agent, event, decision, scenario, sequence)
                    sequence += 1
                    if abs(agent.opinion.purchase_intent - before) >= .05:
                        opinion_changes += 1
                    if decision.action in {"ask_friend", "buy", "reject"}:
                        neighbors = society.neighbors(agent.id)
                        if neighbors:
                            count = min(len(neighbors), rng.randint(1, 3))
                            targets = rng.sample(neighbors, count)
                            sentiment = .8 if decision.action == "buy" else -.65 if decision.action == "reject" else (.4 if agent.opinion.trust >= .5 else -.25)
                            kind = "peer_purchase" if decision.action == "buy" else "peer_rejection" if decision.action == "reject" else "friend_recommendation"
                            followup = SimulationEvent(id=f"event_{sequence:06d}", day=min(config.days, day + rng.randint(1, 2)), event_type=kind,
                                target_agent_ids=targets, source_agent_id=agent.id, intensity=clamp(agent.opinion.recommendation_intent + .35), sentiment=sentiment)
                            if followup.day > day:
                                scheduler.schedule(followup)
                            self._apply_social_influence(agent, targets, by_id, society, followup, sequence)
                            sequence += 1
            self._daily_drift(agents, rng)
            if progress:
                progress(day, config.days, f"Day {day}: {len(decisions)} reactions")
            await asyncio.sleep(0)
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        summary = analyze(run_id, config.seed, config.days, agents, decisions, society.graph, opinion_changes)
        return SimulationResult(run_id, datetime.now(timezone.utc).isoformat(), scenario, config, agents, society, events, decisions, summary)

    def _update_agent(self, agent: Agent, event: SimulationEvent, decision: Decision, scenario: ProductScenario, sequence: int) -> None:
        f = decision.factors
        agent.opinion.awareness = clamp(agent.opinion.awareness + .18 * event.intensity)
        agent.opinion.interest = clamp(agent.opinion.interest * .72 + f["interest"] * .28 + event.sentiment * .05)
        agent.opinion.trust = clamp(agent.opinion.trust * .7 + f["trust"] * .3 + event.sentiment * .08)
        agent.opinion.perceived_value = clamp((agent.opinion.interest + agent.opinion.trust + f["goal"]) / 3)
        agent.opinion.price_acceptance = clamp(f["financial"])
        action_effect = {"buy": .22, "try_free": .12, "research": .04, "ask_friend": .02, "ignore": -.04, "reject": -.13}[decision.action]
        agent.opinion.purchase_intent = clamp(agent.opinion.purchase_intent * .65 + (.3*f["interest"] + .25*f["trust"] + .25*f["financial"] + .2*f["social"]) * .35 + action_effect)
        agent.opinion.recommendation_intent = clamp((agent.opinion.purchase_intent + agent.opinion.trust) / 2 - .12)
        agent.state.product_awareness = agent.opinion.awareness
        agent.state.product_trust = agent.opinion.trust
        agent.state.current_interest = agent.opinion.interest
        emotional = .6 if decision.action in {"buy", "try_free"} else -.5 if decision.action == "reject" else event.sentiment * .5
        agent.remember(Memory(id=f"memory_{sequence:07d}", day=event.day, event_type=event.event_type,
            content=f"{event.event_type.replace('_', ' ')} led to {decision.action.replace('_', ' ')} for {scenario.name}.",
            importance=clamp(.35 + event.intensity * .45), emotional_weight=emotional, source_agent_id=event.source_agent_id))

    def _apply_social_influence(self, speaker: Agent, target_ids: list[str], by_id: dict[str, Agent], society: SocietyGraph, event: SimulationEvent, sequence: int) -> None:
        for offset, target_id in enumerate(target_ids):
            listener = by_id[target_id]
            shift, effect = influence_shift(listener, society.edge(speaker.id, target_id), max(speaker.opinion.trust, .25), event.sentiment, event.intensity)
            listener.opinion.trust = clamp(listener.opinion.trust + shift)
            listener.opinion.interest = clamp(listener.opinion.interest + shift * .65)
            listener.state.peer_pressure = clamp(listener.state.peer_pressure + abs(shift))
            listener.remember(Memory(id=f"memory_{sequence + offset:07d}", day=event.day, event_type=event.event_type,
                content=f"{speaker.name} shared an opinion; effect was {effect}.", importance=clamp(.45 + abs(shift)),
                emotional_weight=shift, source_agent_id=speaker.id))

    def _daily_drift(self, agents: list[Agent], rng) -> None:
        for agent in agents:
            agent.state.mood = clamp(agent.state.mood + rng.uniform(-.025, .025))
            agent.state.motivation = clamp(agent.state.motivation + rng.uniform(-.02, .02))
            agent.state.peer_pressure *= .93
            agent.state.urgency *= .98

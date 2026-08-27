from __future__ import annotations

import math
import random

from crowdforge.agents.models import Agent
from crowdforge.behavior.modifiers import all_modifiers
from crowdforge.simulation.models import Action, Decision, ProductScenario, SimulationEvent


ACTIONS: tuple[Action, ...] = ("buy", "try_free", "research", "ask_friend", "ignore", "reject")


class BehaviorEngine:
    """Compositional probabilistic decision engine with inspectable factors."""

    def evaluate(self, agent: Agent, scenario: ProductScenario, event: SimulationEvent, rng: random.Random) -> Decision:
        f = all_modifiers(agent, scenario, event)
        scores = {
            "buy": -1.2 + 1.25*f["interest"] + 1.15*f["financial"] + .9*f["trust"] + .5*f["social"] + .45*f["urgency"] + .35*f["contradiction"],
            "try_free": -.25 + .8*f["interest"] + .45*(1-f["financial"]) + .35*f["novelty"] + .2*f["trust"],
            "research": .05 + .65*f["interest"] + .6*(1-f["trust"]) + .55*agent.personality.skepticism + .25*f["risk"],
            "ask_friend": -.05 + .7*f["social"] + .55*f["interest"] + .4*(1-f["trust"]),
            "ignore": .15 + .95*(1-f["interest"]) + .35*agent.habit_strength - .25*f["urgency"],
            "reject": -.4 + .75*(1-f["financial"]) + .85*(1-f["trust"]) + .35*agent.privacy_sensitivity - .45*f["interest"],
        }
        # Gumbel-like softmax: compositional scores become a distribution, then seeded sampling decides.
        peak = max(scores.values())
        exp = {action: math.exp((score - peak) / .72) for action, score in scores.items()}
        total = sum(exp.values())
        probabilities = {action: value / total for action, value in exp.items()}
        action = rng.choices(list(probabilities), weights=list(probabilities.values()), k=1)[0]
        positives = sorted(f.items(), key=lambda item: item[1], reverse=True)[:2]
        negatives = sorted(f.items(), key=lambda item: item[1])[:2]
        explanation = [f"+ {name.replace('_', ' ')} ({value:.2f})" for name, value in positives]
        explanation += [f"- weak {name.replace('_', ' ')} ({value:.2f})" for name, value in negatives]
        return Decision(agent_id=agent.id, day=event.day, action=action, probabilities=probabilities, factors=f, explanation=explanation)

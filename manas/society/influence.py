from __future__ import annotations

from manas.agents.models import Agent
from manas.utils.random import clamp


def influence_shift(listener: Agent, edge: dict, speaker_confidence: float, sentiment: float, intensity: float) -> tuple[float, str]:
    susceptibility = listener.personality.social_conformity * .6 + listener.trust_tendency * .4
    base = edge["trust"] * edge["strength"] * edge["influence"] * speaker_confidence * intensity * susceptibility
    disagreement = abs(listener.opinion.trust - ((sentiment + 1) / 2))
    if disagreement > .7 and listener.personality.skepticism > .7:
        return clamp(-sentiment * base * .18, -.15, .15), "backfire"
    shift = clamp(sentiment * base * .28, -.22, .22)
    effect = "reinforcement" if (sentiment >= 0) == (listener.opinion.trust >= .5) else "partial shift"
    if abs(shift) < .015:
        effect = "no effect"
    return shift, effect

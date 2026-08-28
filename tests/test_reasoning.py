import asyncio

from manas.population.generator import PopulationGenerator
from manas.reasoning.base import ReasoningResult
from manas.reasoning.router import ReasoningRouter
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import Decision, ProductScenario, SimulationConfig, SimulationEvent


class FailingReasoner:
    async def reason(self, agent, event, context):
        raise RuntimeError("model unavailable")


class RecordingReasoner:
    def __init__(self):
        self.calls = 0

    async def reason(self, agent, event, context):
        self.calls += 1
        return ReasoningResult(reason="I am torn, but this is my choice.")


def decision(**updates):
    values = {
        "agent_id": "agent_00001",
        "day": 1,
        "action": "search_reviews",
        "probabilities": {"search_reviews": .52, "wait_for_discount": .48},
        "factors": {},
        "explanation": ["I need more evidence."],
        "motivations": [],
    }
    values.update(updates)
    return Decision(**values)


def test_router_only_calls_model_for_ambiguous_or_conflicted_decisions():
    reasoner = RecordingReasoner()
    router = ReasoningRouter(reasoner)
    agent = PopulationGenerator(1).generate(1)[0]
    event = SimulationEvent(id="event", day=1, event_type="product_seen", target_agent_ids=[agent.id])
    result = asyncio.run(router.reason(agent, event, {"decision": decision()}))
    assert reasoner.calls == 1
    assert result.reason

    clear = decision(probabilities={"reject": .9, "search_reviews": .1}, action="reject")
    asyncio.run(router.reason(agent, event, {"decision": clear}))
    assert reasoner.calls == 1


def test_model_failure_falls_back_without_crashing_simulation():
    scenario = ProductScenario(name="Notebook", description="A paper notebook")
    config = SimulationConfig(population_size=8, days=2, seed=7)
    result = asyncio.run(SimulationEngine(reasoning=ReasoningRouter(FailingReasoner())).run(scenario, config))
    assert result.summary.population_size == 8
    assert result.decisions

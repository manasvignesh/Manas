import asyncio
import math

from manas.analytics.segments import analyze_segments, strongest_segments
from manas.scenarios import parse_scenario
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import SimulationConfig


def test_segment_analysis_uses_multiple_dimensions_and_rejects_tiny_groups():
    scenario = parse_scenario("AI fitness coach for Indian college students at INR 399/month")
    result = asyncio.run(SimulationEngine().run(
        scenario, SimulationConfig(population_size=100, days=8, seed=42)
    ))
    segments = analyze_segments(result.agents, scenario)
    minimum = max(5, math.ceil(len(result.agents) * .05))
    assert len({segment.dimension for segment in segments}) >= 6
    assert all(segment.size >= minimum for segment in segments)
    strongest, weakest = strongest_segments(result.agents, scenario)
    assert strongest.size >= minimum
    assert weakest.size >= minimum
    assert strongest.label not in {"Small Business Owner", "Farmer"} or strongest.difference > .02

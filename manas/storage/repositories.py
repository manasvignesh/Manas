from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from manas.agents.models import Agent
from manas.simulation.engine import SimulationResult
from manas.simulation.models import Decision, ProductScenario, SimulationConfig, SimulationEvent, SimulationSummary
from manas.society.graph import SocietyGraph
from manas.society.models import CommunityInsight, InformationItem, OpinionCascade, SocialInteraction
from manas.storage.database import Database


def dump(model) -> str:
    return model.model_dump_json()


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    scenario_name: str
    price: float
    pricing_model: str
    population_size: int
    days: int
    pinned: bool = False


class SimulationRepository:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.initialize()

    def save(self, result: SimulationResult) -> None:
        with self.database.connect() as connection:
            connection.execute("INSERT INTO simulations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (result.run_id, result.created_at, result.config.seed, len(result.agents), result.config.days,
                 dump(result.scenario), dump(result.config), dump(result.summary)))
            connection.executemany("INSERT INTO agents VALUES (?, ?, ?)", [(result.run_id, a.id, dump(a)) for a in result.agents])
            connection.executemany("INSERT INTO relationships VALUES (?, ?, ?, ?)",
                [(result.run_id, a, b, json.dumps(data, sort_keys=True)) for a, b, data in result.graph.graph.edges(data=True)])
            connection.executemany("INSERT INTO events VALUES (?, ?, ?, ?)", [(result.run_id, e.id, e.day, dump(e)) for e in result.events])
            connection.executemany("INSERT INTO actions VALUES (?, ?, ?, ?, ?)", [(result.run_id, i, d.agent_id, d.day, dump(d)) for i, d in enumerate(result.decisions)])
            connection.executemany("INSERT INTO information_items VALUES (?, ?, ?)", [(result.run_id, item.id, dump(item)) for item in (result.information or [])])
            connection.executemany("INSERT INTO social_interactions VALUES (?, ?, ?)", [(result.run_id, item.id, dump(item)) for item in (result.social_interactions or [])])
            connection.executemany("INSERT INTO cascades VALUES (?, ?, ?)", [(result.run_id, item.information_id, dump(item)) for item in (result.cascades or [])])
            connection.executemany("INSERT INTO community_insights VALUES (?, ?, ?)", [(result.run_id, item.name, dump(item)) for item in (result.communities or [])])

    def list_runs(self) -> list[SimulationSummary]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT summary_json FROM simulations ORDER BY created_at DESC").fetchall()
        return [SimulationSummary.model_validate_json(row[0]) for row in rows]

    def list_run_records(self) -> list[RunRecord]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT s.*, p.simulation_id AS pinned FROM simulations s LEFT JOIN pinned_runs p ON p.simulation_id = s.id ORDER BY s.created_at DESC").fetchall()
        records = []
        for row in rows:
            scenario = ProductScenario.model_validate_json(row["scenario_json"])
            records.append(RunRecord(row["id"], row["created_at"], scenario.name, scenario.price, scenario.pricing_model,
                                     row["population_size"], row["days"], bool(row["pinned"])))
        return records

    def resolve_run_id(self, reference: str) -> str:
        records = self.list_run_records()
        if not records:
            raise KeyError("No simulations have been saved yet.")
        normalized = reference.strip().casefold()
        if normalized in {"latest", "last"}: return records[0].run_id
        if normalized == "previous" and len(records) > 1: return records[1].run_id
        if normalized == "pinned":
            pinned = next((item for item in records if item.pinned), None)
            if pinned: return pinned.run_id
        if normalized.isdigit() and 1 <= int(normalized) <= len(records): return records[int(normalized) - 1].run_id
        if any(item.run_id == reference for item in records): return reference
        raise KeyError(f"Unknown run reference: {reference}")

    def pin(self, reference: str, pinned: bool = True) -> str:
        run_id = self.resolve_run_id(reference)
        with self.database.connect() as connection:
            if pinned:
                connection.execute("INSERT OR REPLACE INTO pinned_runs VALUES (?, ?)", (run_id, datetime.now(timezone.utc).isoformat()))
            else:
                connection.execute("DELETE FROM pinned_runs WHERE simulation_id = ?", (run_id,))
        return run_id

    def load(self, run_id: str) -> SimulationResult:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM simulations WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(f"Simulation not found: {run_id}")
            agents = [Agent.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM agents WHERE simulation_id = ? ORDER BY agent_id", (run_id,))]
            events = [SimulationEvent.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM events WHERE simulation_id = ? ORDER BY day, event_id", (run_id,))]
            decisions = [Decision.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM actions WHERE simulation_id = ? ORDER BY sequence", (run_id,))]
            edge_rows = connection.execute("SELECT source_id, target_id, data_json FROM relationships WHERE simulation_id = ?", (run_id,)).fetchall()
            information = [InformationItem.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM information_items WHERE simulation_id = ?", (run_id,))]
            interactions = [SocialInteraction.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM social_interactions WHERE simulation_id = ?", (run_id,))]
            cascades = [OpinionCascade.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM cascades WHERE simulation_id = ?", (run_id,))]
            communities = [CommunityInsight.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM community_insights WHERE simulation_id = ?", (run_id,))]
        config = SimulationConfig.model_validate_json(row["config_json"])
        graph = SocietyGraph(config.seed)
        for agent in agents:
            graph.graph.add_node(agent.id)
        for edge in edge_rows:
            graph.graph.add_edge(edge[0], edge[1], **json.loads(edge[2]))
        return SimulationResult(run_id, row["created_at"], ProductScenario.model_validate_json(row["scenario_json"]), config,
                                agents, graph, events, decisions, SimulationSummary.model_validate_json(row["summary_json"]),
                                information, interactions, cascades, communities)

from __future__ import annotations

import json

from crowdforge.agents.models import Agent
from crowdforge.simulation.engine import SimulationResult
from crowdforge.simulation.models import Decision, ProductScenario, SimulationConfig, SimulationEvent, SimulationSummary
from crowdforge.society.graph import SocietyGraph
from crowdforge.storage.database import Database


def dump(model) -> str:
    return model.model_dump_json()


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

    def list_runs(self) -> list[SimulationSummary]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT summary_json FROM simulations ORDER BY created_at DESC").fetchall()
        return [SimulationSummary.model_validate_json(row[0]) for row in rows]

    def load(self, run_id: str) -> SimulationResult:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM simulations WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(f"Simulation not found: {run_id}")
            agents = [Agent.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM agents WHERE simulation_id = ? ORDER BY agent_id", (run_id,))]
            events = [SimulationEvent.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM events WHERE simulation_id = ? ORDER BY day, event_id", (run_id,))]
            decisions = [Decision.model_validate_json(r[0]) for r in connection.execute("SELECT data_json FROM actions WHERE simulation_id = ? ORDER BY sequence", (run_id,))]
            edge_rows = connection.execute("SELECT source_id, target_id, data_json FROM relationships WHERE simulation_id = ?", (run_id,)).fetchall()
        config = SimulationConfig.model_validate_json(row["config_json"])
        graph = SocietyGraph(config.seed)
        for agent in agents:
            graph.graph.add_node(agent.id)
        for edge in edge_rows:
            graph.graph.add_edge(edge[0], edge[1], **json.loads(edge[2]))
        return SimulationResult(run_id, row["created_at"], ProductScenario.model_validate_json(row["scenario_json"]), config,
                                agents, graph, events, decisions, SimulationSummary.model_validate_json(row["summary_json"]))

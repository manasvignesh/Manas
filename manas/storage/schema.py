SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS simulations (
    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, seed INTEGER NOT NULL,
    population_size INTEGER NOT NULL, days INTEGER NOT NULL,
    scenario_json TEXT NOT NULL, config_json TEXT NOT NULL, summary_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
    simulation_id TEXT NOT NULL, agent_id TEXT NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, agent_id), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS relationships (
    simulation_id TEXT NOT NULL, source_id TEXT NOT NULL, target_id TEXT NOT NULL, data_json TEXT NOT NULL,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS events (
    simulation_id TEXT NOT NULL, event_id TEXT NOT NULL, day INTEGER NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, event_id), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS actions (
    simulation_id TEXT NOT NULL, sequence INTEGER NOT NULL, agent_id TEXT NOT NULL, day INTEGER NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, sequence), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS information_items (
    simulation_id TEXT NOT NULL, information_id TEXT NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, information_id), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS social_interactions (
    simulation_id TEXT NOT NULL, interaction_id TEXT NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, interaction_id), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS cascades (
    simulation_id TEXT NOT NULL, information_id TEXT NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, information_id), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS community_insights (
    simulation_id TEXT NOT NULL, name TEXT NOT NULL, data_json TEXT NOT NULL,
    PRIMARY KEY (simulation_id, name), FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS pinned_runs (
    simulation_id TEXT PRIMARY KEY, pinned_at TEXT NOT NULL,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
"""

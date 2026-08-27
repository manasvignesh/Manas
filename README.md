# MANAS

**One idea. Many synthetic perspectives.**

MANAS is a local-first CLI and terminal application that creates a persistent synthetic society, introduces a product idea, and lets opinions evolve through probabilistic behavior and social interaction. It is useful for discovering plausible objections, motivations, segments, and second-order effects before real research.

MANAS is **not** an oracle, a survey, or a replacement for talking to people. Its output describes an experimental synthetic population under explicit assumptions—not real market statistics.

## Quick start

Requires Python 3.11 or newer.

```bash
pip install -e .
manas init
manas simulate --idea "AI fitness coach" --population 100 --days 30 --seed 42 --price 399 --pricing-model monthly
```

Launch the Textual interface with:

```bash
manas
```

No API key, cloud account, or local language model is required.

## Commands

```text
manas init
manas simulate [--idea ...] [--population 100] [--days 30] [--seed 42]
manas replay RUN_ID [--price 199]
manas compare RUN_A RUN_B
manas agents RUN_ID
manas export RUN_ID --formats json,csv,markdown
manas settings
manas info
```

`--debug` exposes the latest structured decision distribution and modifiers. Fixed seeds make non-AI runs reproducible.

## What is simulated

Each person has persistent identity, demographic context, personality, values, goals, financial context, contradictions, dynamic state, multidimensional product opinion, relationships, and compact decaying memories. Agents are computational entities—not prompts.

The India V1 population pack uses configurable synthetic distributions across regions, urbanicity, occupation, education, income, language, household structure, technology familiarity, and interests. It is intentionally labeled experimental and does not claim census accuracy.

The social network uses homophily and community structure with cross-group weak ties. Only agents affected by scheduled or propagated events are evaluated. Decisions come from separate interest, financial, trust, social, memory, goal, emotion, contradiction, urgency, novelty, and risk modifiers, combined into an action distribution and sampled using seeded randomness.

## Architecture

```text
population pack → persistent agents → clustered society graph
                                       ↓
event scheduler → behavior modifiers → action distribution
                                       ↓
                  memories ← opinion evolution → social propagation
                                       ↓
                             analytics → SQLite / exports
```

The package separates `agents`, `population`, `society`, `behavior`, `simulation`, `reasoning`, `analytics`, `storage`, and `cli`. `ReasoningEngine` is provider-neutral; the default is a no-op, a deterministic mock is included, and `LocalReasoningEngine` accepts any structured JSON provider. MANAS never downloads a model implicitly.

## Data and privacy

Local configuration and SQLite data default to `~/.manas/`. Set `MANAS_HOME` to use another directory. Exported JSON, CSV, and Markdown are written only when requested.

## Screenshots

Terminal screenshots will be added as the interface evolves.

## Development

```bash
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Useful next steps include additional population packs and scenarios, calibrated behavioral modules, richer comparison views, independent data-pack updates, and optional local/provider reasoning adapters.

## Disclaimer

Synthetic results are exploratory artifacts. Validate decisions with real users, representative research, domain expertise, and appropriate ethical review. Do not use MANAS output to make high-stakes decisions about individuals.

## License

Apache-2.0.

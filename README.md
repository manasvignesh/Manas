# MANAS

**Many Agents, Networked Adaptive Society**

**One idea. Many minds.**

MANAS is an open-source, local-first synthetic society simulation engine. Introduce a product, service, feature, policy, or other scenario and explore how many persistent synthetic individuals might plausibly respond as they encounter it, discuss it, and change their minds.

MANAS is an exploratory tool—not an oracle, survey, or replacement for real people. Its results describe a synthetic population under selected assumptions and are not real-world market statistics.

## Quick start

MANAS requires Python 3.11 or newer.

```bash
pip install -e ".[dev]"
manas init
manas
```

Running `manas` opens a minimal conversational flow. It asks one question at a time and uses the same simulation API as scriptable commands.

No API key, cloud account, or language model is required.

## Non-interactive simulation

```bash
manas simulate \
  --idea "AI fitness coach for Indian college students" \
  --population 100 \
  --days 30 \
  --seed 42 \
  --price 399 \
  --pricing-model monthly
```

You can also run MANAS as a Python module:

```bash
python -m manas
```

## Commands

```text
manas
manas init
manas simulate
manas replay RUN_ID
manas compare RUN_A RUN_B
manas agents RUN_ID [--search NAME]
manas export RUN_ID --formats json,csv,markdown
manas models
manas settings
manas info
```

Use `manas simulate --debug` to inspect action probabilities, behavioral modifiers, and structured explanations. Normal output filters internal mechanics and surfaces only milestones, notable reactions, and emerging signals.

Fixed seeds make non-AI runs reproducible. Replays regenerate the same base society and seed while applying controlled scenario changes.

## What MANAS simulates

Each synthetic person has persistent identity, demographic and financial context, personality, values, goals, contradictions, dynamic state, multidimensional product opinions, relationships, and compact memories that decay in relevance.

The experimental India V1 population pack generates variation across region, urbanicity, occupation, education, income, language, household structure, technology familiarity, and interests. It does not claim census accuracy.

The NetworkX society graph uses homophily, communities, and cross-group weak ties. The event-driven runtime evaluates only affected agents. Behavior is assembled from separate interest, financial, trust, social, memory, goal, emotion, contradiction, urgency, novelty, and risk modifiers, producing an inspectable probability distribution before seeded sampling.

```text
population pack -> persistent agents -> clustered society graph
                                        |
event scheduler -> behavior modifiers -> action distribution
                                        |
                   memories <- opinion evolution -> social propagation
                                        |
                              analytics -> SQLite / exports
```

Core simulation modules never print terminal output. The Rich/Typer presentation layer decides what users see.

## Optional local models

The core engine runs without a model. `manas models` can discover installed Ollama models, GGUF files, llama.cpp-compatible files, and manually configured paths. It also inspects CPU, RAM, available disk, and supported GPU information before offering model-class guidance.

MANAS never downloads or deletes a model file without explicit user action. The provider-neutral `ReasoningEngine` remains an optional enhancement for ambiguity and natural-language nuance.

## Storage and migration

Configuration and SQLite data default to `~/.manas/`. Set `MANAS_HOME` to use another directory.

During `manas init`, development data under `~/.crowdforge/` can be detected and copied after confirmation. The original directory is preserved. The temporary `crowdforge` command prints a rename notice and directs users to `manas`; it does not maintain a second implementation.

Exports are written only when requested and support JSON, CSV, and Markdown.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The test suite covers population generation, social graph integrity, memory decay, behavior distributions, seeded reproducibility, event integrity, SQLite round trips, interactive setup, CLI flows, module execution, exports, replay/comparison, model discovery, and absence of Textual.

See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting behavior or population changes. New population packs must document assumptions and limitations. New behavior factors must remain inspectable.

## Disclaimer

Synthetic results are exploratory artifacts. Validate decisions with real users, representative research, domain expertise, and appropriate ethical review. Do not use MANAS output to make high-stakes decisions about individuals.

## License

MIT. See [LICENSE](LICENSE).

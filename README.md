# MANAS

**Many Agents, Networked Adaptive Society**

**One idea. Many minds.**

MANAS is a local-first synthetic society simulator. Type one idea, introduce it to persistent fictional people, and watch different interpretations, conflicts, social messages, memories, and decisions emerge.

```console
$ manas

MANAS
Many Agents, Networked Adaptive Society

One idea. Many minds.

What do you want to explore?

> AI fitness coach for Indian college students at INR 399/month
```

MANAS offers perspectives, not predictions. It is not a survey, demand forecast, or substitute for research with real people. Every reported percentage describes a synthetic world under explicit assumptions.

## Install

MANAS requires Python 3.11 or newer. A virtual environment keeps the install isolated and makes `manas` available while that environment is active.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
manas init
manas
```

If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or use `.venv\Scripts\python -m manas` directly.

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
manas init
manas
```

No API key, cloud account, or language model is required.

## The experience

MANAS parses an idea into a structured scenario, builds 100 fictional people across the experimental India V1 population pack, connects them into social circles, and advances an event-driven 14-day society. It asks only for missing essentials; population, region, duration, and random seed use beginner-friendly defaults.

Example result:

```text
WHAT MANAS FOUND

Strongest pull
Current goals appeared in positive consideration paths.

Biggest resistance
Price and trust created hesitation and comparison behavior.

Social effect
A concern moved through two connected circles, but people reacted differently.

What you should test with real people
- a student tier or free trial
- privacy expectations around health data
- whether personalization feels better than free content
```

The wording is generated from actual simulation state. MANAS does not invent events to make a better story.

## Explore and replay

Run IDs remain internal; readable aliases work in everyday commands:

```bash
manas runs
manas agents latest --search Priya
manas replay latest --price 199
manas compare previous latest
manas export latest --formats json,csv,markdown
```

Inside the conversational home, `/runs`, `/models`, `/settings`, `/help`, and `/exit` are available. After a run, a natural change such as `price to 199` creates a seeded replay of the same society so the comparison can explain who changed and why.

## What makes a synthetic person

Agents have persistent identities, correlated tendencies, goals, values, active life situations, category experience, contradictions, evolving emotional and financial state, and semantic memories. The same product passes through separate perception, motivational-conflict, consideration-set, and decision-dynamics stages. High income cannot manufacture relevance, and privacy concern does not force everyone into rejection.

Social interactions record the speaker, listener, relationship, transmitted claim, credibility, reaction, and result. Information can spread, mutate, cross social circles, and form detectable cascades. NetworkX provides the clustered society graph; SQLite stores complete local runs.

## Optional local reasoning

```bash
manas models
```

The model manager detects local GGUF/llama.cpp and Ollama models, inspects system resources, and can install one small curated GGUF model only after explicit confirmation. Downloads support resume, checksum validation, temporary files, and atomic completion.

Local reasoning is selective. It may express an already-made ambiguous decision in more natural language, but it never replaces the native behavior engine. If inference fails, MANAS logs the failure and continues. No API key or cloud processing is needed.

## Scripted usage

```bash
manas simulate \
  --idea "AI fitness coach for Indian college students at INR 399/month" \
  --population 100 \
  --days 14 \
  --seed 42

manas benchmark
python -m manas
```

`manas benchmark` checks affordability sensitivity, relevance over irrelevant wealth, trusted-peer influence, seed variation, and motivational contradiction handling. These are behavioral invariants, not empirical calibration.

Use `--debug` on scripted simulation and replay commands to expose technical failures and internal numeric factors. Normal output keeps implementation mechanics out of the human story.

## Population data and limitations

India V1 is explicitly experimental and uncalibrated. Metadata under `data/populations/india/` separates future sourced data from current synthetic assumptions. It contains no claimed census or consumer statistics. Do not use MANAS for high-stakes decisions about individuals or groups.

Validate important findings with representative user research, domain expertise, and appropriate ethical review.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

The suite includes behavior, diversity, life context, perception, motivation, memory, propagation, cascades, run aliases, replay parsing, model downloads, reasoning fallback, CLI, Windows paths, calibration benchmarks, and 100-person golden scenarios.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing behavior or population changes.

## License

Apache License 2.0. See [LICENSE](LICENSE).

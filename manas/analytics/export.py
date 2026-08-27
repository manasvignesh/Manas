from __future__ import annotations

import csv
import json
from pathlib import Path

from manas.simulation.engine import SimulationResult


def export_result(result: SimulationResult, output_dir: Path, formats: set[str]) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    if "json" in formats:
        path = output_dir / f"{result.run_id}.json"
        payload = {
            "metadata": {"run_id": result.run_id, "created_at": result.created_at},
            "scenario": result.scenario.model_dump(mode="json"), "config": result.config.model_dump(mode="json"),
            "summary": result.summary.model_dump(mode="json"),
            "agents": [a.model_dump(mode="json") for a in result.agents],
            "events": [e.model_dump(mode="json") for e in result.events],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        created.append(path)
    if "csv" in formats:
        path = output_dir / f"{result.run_id}_agents.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "name", "age", "location", "occupation", "income_band", "sentiment", "awareness", "interest", "trust", "purchase_intent"])
            writer.writeheader()
            for a in result.agents:
                writer.writerow({"id": a.id, "name": a.name, "age": a.age, "location": a.location, "occupation": a.occupation,
                    "income_band": a.income_band, "sentiment": a.opinion.sentiment, "awareness": a.opinion.awareness,
                    "interest": a.opinion.interest, "trust": a.opinion.trust, "purchase_intent": a.opinion.purchase_intent})
        created.append(path)
    if "markdown" in formats or "md" in formats:
        path = output_dir / f"{result.run_id}_summary.md"
        s = result.summary
        insights = "\n".join(f"- {item}" for item in s.insights)
        path.write_text(f"# MANAS simulation: {result.scenario.name}\n\n**Run:** `{s.run_id}`  \n**Seed:** {s.seed}  \n**Population:** {s.population_size}  \n**Days:** {s.days}\n\n## Results\n\n- Average purchase intent: {s.average_purchase_intent:.1%}\n- Positive: {s.sentiment['positive']:.1%}\n- Neutral: {s.sentiment['neutral']:.1%}\n- Negative: {s.sentiment['negative']:.1%}\n\n## Insights\n\n{insights}\n\n> {s.disclaimer}\n", encoding="utf-8")
        created.append(path)
    return created

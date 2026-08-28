from __future__ import annotations

import asyncio
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from manas.agents.models import Agent
from manas.reasoning.base import ReasoningResult
from manas.simulation.models import SimulationEvent


def _prompt(agent: Agent, context: dict[str, Any]) -> str:
    decision = context["decision"]
    return ("Express this already-made synthetic decision in one brief sentence. Do not change the decision. "
            f"Person: {agent.age}, {agent.occupation}, contexts: {[c.situation for c in agent.life_contexts]}. "
            f"Decision: {decision.action}. Reasons: {decision.explanation}. Return JSON: {{\"reason\": \"...\"}}")


class LlamaCppReasoningEngine:
    def __init__(self, model_path: Path, executable: str | None = None) -> None:
        self.model_path = model_path
        self.executable = executable or shutil.which("llama-cli") or shutil.which("llama") or ""

    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        if not self.executable: raise RuntimeError("llama.cpp runtime was not found")
        process = await asyncio.create_subprocess_exec(self.executable, "-m", str(self.model_path), "-p", _prompt(agent, context), "-n", "80", "--simple-io",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45)
        if process.returncode: raise RuntimeError(stderr.decode(errors="replace")[-500:])
        text = stdout.decode(errors="replace")
        start, end = text.find("{"), text.rfind("}")
        payload = json.loads(text[start:end + 1])
        return ReasoningResult(reason=str(payload.get("reason", "")))


class OllamaReasoningEngine:
    def __init__(self, model: str, endpoint: str = "http://127.0.0.1:11434/api/generate") -> None:
        self.model, self.endpoint = model, endpoint

    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        body = json.dumps({"model": self.model, "prompt": _prompt(agent, context), "stream": False, "format": "json"}).encode()
        def request():
            with urllib.request.urlopen(urllib.request.Request(self.endpoint, body, {"Content-Type": "application/json"}), timeout=20) as response:
                return json.loads(response.read())
        payload = await asyncio.to_thread(request)
        parsed = json.loads(payload.get("response", "{}"))
        return ReasoningResult(reason=str(parsed.get("reason", "")))

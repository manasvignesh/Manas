from __future__ import annotations

from pathlib import Path

from manas.reasoning.base import NoOpReasoningEngine, ReasoningEngine
from manas.reasoning.providers import LlamaCppReasoningEngine, OllamaReasoningEngine
from manas.reasoning.router import ReasoningRouter
from manas.utils.config import AppConfig


def build_reasoning_engine(config: AppConfig) -> ReasoningEngine:
    if config.reasoning_engine == "none" or not config.active_model_path:
        return NoOpReasoningEngine()
    if "ollama" in config.reasoning_engine:
        return ReasoningRouter(OllamaReasoningEngine(config.active_model_path))
    path = Path(config.active_model_path).expanduser()
    if path.is_file():
        return ReasoningRouter(LlamaCppReasoningEngine(path))
    return NoOpReasoningEngine()

from __future__ import annotations

from pydantic import BaseModel, Field


class CalibrationRecord(BaseModel):
    """A future comparison between an external observation and a MANAS result."""

    scenario_id: str
    metric: str
    observed_result: float
    predicted_result: float
    source: str
    error_metric: str = "absolute_error"

    @property
    def error(self) -> float:
        return abs(self.observed_result - self.predicted_result)


class ParameterAdjustment(BaseModel):
    parameter: str
    previous_value: float
    proposed_value: float
    evidence_record_ids: list[str] = Field(default_factory=list)
    rationale: str


class BenchmarkResult(BaseModel):
    name: str
    passed: bool
    evidence: str

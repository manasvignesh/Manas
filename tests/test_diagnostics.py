import asyncio

from typer.testing import CliRunner

from manas.calibration import diagnose_result
from manas.cli.app import app
from manas.scenarios import parse_scenario
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import SimulationConfig


runner = CliRunner()


def test_diagnostics_measure_real_run_health():
    result = asyncio.run(SimulationEngine().run(
        parse_scenario("AI fitness coach for Indian college students at INR 399/month"),
        SimulationConfig(population_size=60, days=8, seed=42),
    ))
    checks = diagnose_result(result)
    assert {check.name for check in checks} >= {
        "Target-match distribution", "Dominant modifier check", "Sentiment balance",
        "Topic dominance", "Price sensitivity test", "Segment sample sizes",
    }
    assert all(check.evidence for check in checks)


def test_diagnose_cli_uses_readable_alias(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    run = runner.invoke(app, ["simulate", "--idea", "Fitness app for college students",
                              "--population", "20", "--days", "3", "--seed", "4"])
    assert run.exit_code == 0, run.output
    diagnostic = runner.invoke(app, ["diagnose", "latest"])
    assert diagnostic.exit_code == 0, diagnostic.output
    assert "MANAS DIAGNOSTICS" in diagnostic.output
    assert "Target-match distribution" in diagnostic.output

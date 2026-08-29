import re

from typer.testing import CliRunner

from manas.cli.app import app


runner = CliRunner()


def test_info_and_small_simulation(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    init = runner.invoke(app, ["init"])
    assert init.exit_code == 0
    result = runner.invoke(app, ["simulate", "--idea", "Study planner", "--population", "12", "--days", "3", "--seed", "8"])
    assert result.exit_code == 0, result.output
    assert "Simulation complete" in result.output
    assert "real-world survey statistics" in result.output
    info = runner.invoke(app, ["info"])
    assert info.exit_code == 0
    assert "Stored runs: 1" in info.output


def test_replay_compare_agents_and_export(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    first = runner.invoke(app, ["simulate", "--idea", "Study planner", "--population", "12", "--days", "3", "--seed", "8", "--price", "399"])
    assert first.exit_code == 0, first.output
    run_a = re.search(r"run_\d+_\d+_[a-f0-9]+", first.output)
    assert run_a
    second = runner.invoke(app, ["replay", run_a.group(), "--price", "199"])
    assert second.exit_code == 0, second.output
    run_b = re.search(r"run_\d+_\d+_[a-f0-9]+", second.output)
    assert run_b
    comparison = runner.invoke(app, ["compare", run_a.group(), run_b.group()])
    assert comparison.exit_code == 0
    assert "Scenario comparison" in comparison.output
    explored = runner.invoke(app, ["agents", run_a.group(), "--search", "student"])
    assert explored.exit_code == 0
    output = tmp_path / "exports"
    exported = runner.invoke(app, ["export", run_a.group(), "--output", str(output)])
    assert exported.exit_code == 0
    assert len(list(output.iterdir())) == 3


def test_benchmark_command_reports_all_sanity_checks():
    result = runner.invoke(app, ["benchmark"])
    assert result.exit_code == 0, result.output
    assert result.output.count("PASS") >= 14
    assert "not evidence that MANAS predicts real populations" in result.output


def test_normal_mode_hides_storage_traceback(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))

    class BrokenRepository:
        def save(self, _result):
            raise OSError("synthetic storage failure")

    monkeypatch.setattr("manas.cli.app.repository", lambda: BrokenRepository())
    result = runner.invoke(
        app,
        ["simulate", "--idea", "Study planner", "--population", "4", "--days", "1"],
    )
    assert result.exit_code == 1
    assert "couldn't complete or save" in result.output
    assert "Traceback" not in result.output

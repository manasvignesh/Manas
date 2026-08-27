from typer.testing import CliRunner

from crowdforge.cli.app import app


runner = CliRunner()


def test_info_and_small_simulation(monkeypatch, tmp_path):
    monkeypatch.setenv("CROWDFORGE_HOME", str(tmp_path / "home"))
    init = runner.invoke(app, ["init"])
    assert init.exit_code == 0
    result = runner.invoke(app, ["simulate", "--idea", "Study planner", "--population", "12", "--days", "3", "--seed", "8"])
    assert result.exit_code == 0, result.output
    assert "Simulation complete" in result.output
    assert "real-world survey statistics" in result.output
    info = runner.invoke(app, ["info"])
    assert info.exit_code == 0
    assert "Stored runs: 1" in info.output

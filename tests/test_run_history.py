from typer.testing import CliRunner

from manas.cli.app import app, repository
from manas.cli.prompts import parse_replay_change


runner = CliRunner()


def test_natural_replay_change_parser():
    assert parse_replay_change("price to 199") == ("price", "199")
    assert parse_replay_change("add feature student discount") == ("feature", "student discount")
    assert parse_replay_change("target to college students") == ("target", "college students")
    assert parse_replay_change("run for 21") == ("days", "21")
    assert parse_replay_change("make it nicer") is None


def test_run_aliases_and_pinning(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    for price in (399, 199):
        result = runner.invoke(app, ["simulate", "--idea", "Fitness app", "--population", "10", "--days", "2", "--seed", "7", "--price", str(price)])
        assert result.exit_code == 0, result.output
    repo = repository()
    records = repo.list_run_records()
    assert repo.resolve_run_id("latest") == records[0].run_id
    assert repo.resolve_run_id("previous") == records[1].run_id
    assert repo.resolve_run_id("2") == records[1].run_id
    repo.pin("2")
    assert repo.resolve_run_id("pinned") == records[1].run_id
    listed = runner.invoke(app, ["runs"])
    assert listed.exit_code == 0
    assert "pinned" in listed.output
    run_lines = [line for line in listed.output.splitlines() if line.strip().startswith(("1 ", "2 "))]
    assert "replay" in run_lines[0]
    assert "replay" not in run_lines[1]


def test_home_is_idea_first_not_numbered_menu(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    result = runner.invoke(app, input="/exit\n")
    assert result.exit_code == 0
    assert "What do you want to explore?" in result.output
    assert "1. New simulation" not in result.output

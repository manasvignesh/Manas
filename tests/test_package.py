from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_manas_entry_points_and_module_execution():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["name"] == "manas"
    assert project["project"]["scripts"]["manas"] == "manas.cli.app:app"
    result = subprocess.run([sys.executable, "-m", "manas", "--help"], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "Many Agents, Networked Adaptive Society" in result.stdout


def test_textual_is_not_a_dependency_or_import():
    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()
    package_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "manas").rglob("*.py")).casefold()
    assert "textual" not in project_text
    assert "textual" not in package_text


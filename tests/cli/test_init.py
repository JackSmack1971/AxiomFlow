import sys
from pathlib import Path

import click
import pytest
import yaml
from click.testing import CliRunner

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from axiomflow.cli.init import _run_smoke_test, cli, initialize_project


def test_initialize_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    initialize_project("demo")
    base = tmp_path / "demo"
    for d in ["agents", "workflows", "configs", "configs/secrets"]:
        assert (base / d).exists()
    assert (base / "configs" / "roles.yaml").is_file()
    assert (base / "configs" / "secrets" / ".gitkeep").is_file()
    data = yaml.safe_load((base / "project.yaml").read_text())
    assert data["name"] == "demo"
    assert "created" in data


def test_cli_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, ["init", "demo"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "demo" / "agents").is_dir()


def test_smoke_test_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    base = initialize_project("demo")
    (base / "agents").rmdir()
    with pytest.raises(click.ClickException):
        _run_smoke_test(base)

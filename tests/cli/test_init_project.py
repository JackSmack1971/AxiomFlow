import sys
from pathlib import Path

import yaml
from click.testing import CliRunner

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from axiomflow.cli.init_project import init_project


def test_init_project_creates_structure(tmp_path: Path) -> None:
    secret = tmp_path / "token.txt"
    secret.write_text("s3cr3t")

    runner = CliRunner()
    result = runner.invoke(
        init_project,
        [
            "--name",
            "demo",
            "--owner",
            "alice",
            "--policy",
            "policy1",
            "--secret",
            str(secret),
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    for d in ["agents", "adapters", "workflows", "evaluators", "secrets"]:
        assert (tmp_path / d).is_dir()
    data = yaml.safe_load((tmp_path / "project.yaml").read_text())
    assert data["owner"] == "alice"
    assert data["rbac"]["users"]["alice"] == ["admin"]
    assert (tmp_path / "secrets" / "token.txt").read_text() == "s3cr3t"

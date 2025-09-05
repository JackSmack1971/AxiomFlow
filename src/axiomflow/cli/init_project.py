from __future__ import annotations

import shutil
from pathlib import Path
from typing import Sequence

import click
import yaml


@click.command("init-project")
@click.option("--name", required=True, help="Name of the project.")
@click.option("--owner", required=True, help="Owner of the project.")
@click.option(
    "--policy",
    "policies",
    multiple=True,
    help="Policy identifiers to apply to the project.",
)
@click.option(
    "--secret",
    "secrets",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
    help="Paths to secret files to mount into the project.",
)
@click.argument(
    "directory", type=click.Path(file_okay=False, path_type=Path), default=Path(".")
)
def init_project(
    name: str,
    owner: str,
    policies: Sequence[str],
    secrets: Sequence[Path],
    directory: Path,
) -> None:
    """Initialize a new AxiomFlow project."""
    directory.mkdir(parents=True, exist_ok=True)

    dirs = [
        "agents",
        "adapters",
        "workflows",
        "evaluators",
        "secrets",
    ]
    for d in dirs:
        (directory / d).mkdir(exist_ok=True)

    for secret_path in secrets:
        target = directory / "secrets" / secret_path.name
        shutil.copyfile(secret_path, target)
        click.echo(f"Mounted secret {secret_path.name}")

    project_config = {
        "name": name,
        "owner": owner,
        "policies": list(policies),
        "rbac": {
            "roles": {"admin": {"permissions": ["*"]}},
            "users": {owner: ["admin"]},
        },
    }
    config_path = directory / "project.yaml"
    config_path.write_text(yaml.safe_dump(project_config, sort_keys=False))

    _run_smoke_test(directory, owner)
    click.echo("Project initialized")


def _run_smoke_test(base_dir: Path, owner: str) -> None:
    try:
        config_path = base_dir / "project.yaml"
        data = yaml.safe_load(config_path.read_text())
        required = [
            "agents",
            "adapters",
            "workflows",
            "evaluators",
            "secrets",
        ]
        missing = [d for d in required if not (base_dir / d).is_dir()]
        if missing:
            raise click.ClickException(f"missing directories: {', '.join(missing)}")
        if data.get("owner") != owner:
            raise click.ClickException("owner mismatch")
    except Exception as exc:  # pragma: no cover - unexpected failures
        raise click.ClickException(f"Smoke test failed: {exc}") from exc

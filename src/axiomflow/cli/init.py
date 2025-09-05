from __future__ import annotations

import datetime as _dt
from pathlib import Path

import click
import yaml

SKELETON_DIRS = ["agents", "workflows", "configs", "configs/secrets"]


def initialize_project(project_name: str) -> Path:
    """Create a new AxiomFlow project skeleton.

    Args:
        project_name: Name of the project to create.

    Returns:
        Path to the created project directory.
    """
    base_dir = Path(project_name).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    for directory in SKELETON_DIRS:
        (base_dir / directory).mkdir(parents=True, exist_ok=True)

    roles_path = base_dir / "configs" / "roles.yaml"
    if not roles_path.exists():
        roles_path.write_text("roles:\n  admin:\n    permissions:\n      - '*'\n")

    secrets_dir = base_dir / "configs" / "secrets"
    (secrets_dir / ".gitkeep").touch(exist_ok=True)

    project_yaml = {
        "name": project_name,
        "created": _dt.datetime.utcnow().isoformat(),
        "metadata": {},
    }
    (base_dir / "project.yaml").write_text(
        yaml.safe_dump(project_yaml, sort_keys=False)
    )

    _run_smoke_test(base_dir)
    return base_dir


def _run_smoke_test(base_dir: Path) -> None:
    required = ["agents", "workflows", "configs", "configs/secrets"]
    missing = [d for d in required if not (base_dir / d).is_dir()]
    if missing:
        raise click.ClickException(f"missing directories: {', '.join(missing)}")
    if not (base_dir / "project.yaml").is_file():
        raise click.ClickException("project.yaml not found")
    if not (base_dir / "configs" / "roles.yaml").is_file():
        raise click.ClickException("roles.yaml missing")


@click.group()
def cli() -> None:
    """AxiomFlow command line interface."""


@cli.command()
@click.argument("project_name")
def init(project_name: str) -> None:
    """Initialize a new AxiomFlow project."""
    initialize_project(project_name)
    click.echo(f"Initialized project {project_name}")

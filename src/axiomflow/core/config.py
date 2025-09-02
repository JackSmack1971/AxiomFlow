"""Pydantic models for orchestrator configuration.

These schemas load and validate the ``configs/orchestrator.yaml`` file,
ensuring that orchestrator settings are treated as code and validated at
runtime.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class RoutingPolicy(BaseModel):
    """Route tasks to specific agents."""

    task: str
    agent: str


class OrchestratorConfig(BaseModel):
    """Runtime parameters for the orchestrator.

    The schema enforces configuration as code by validating and typing
    the orchestrator settings defined in ``configs/orchestrator.yaml``.
    Developers can reason about configuration changes similarly to
    code changes.
    """

    workflow_timeout: int = Field(
        ..., gt=0, description="Maximum seconds a workflow may run"
    )
    default_agent: str
    routing_policies: List[RoutingPolicy] = Field(default_factory=list)
    api_key: str | None = None

    @classmethod
    def load(cls, path: Path) -> "OrchestratorConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the orchestrator YAML file.

        Returns:
            Parsed and validated ``OrchestratorConfig`` instance.

        Raises:
            ValidationError: If the YAML content does not conform to the schema.
        """
        raw = path.read_text()
        expanded = os.path.expandvars(raw)
        data = yaml.safe_load(expanded)
        return cls.model_validate(data["orchestrator"])


def load_orchestrator_config(path: Path | None = None) -> OrchestratorConfig:
    """Convenience function to load orchestrator configuration.

    Args:
        path: Optional path to the YAML configuration. Defaults to
            ``configs/orchestrator.yaml``.

    Returns:
        An ``OrchestratorConfig`` instance loaded from the specified file.
    """
    if path is None:
        path = Path(__file__).resolve().parents[3] / "configs" / "orchestrator.yaml"
    return OrchestratorConfig.load(path)

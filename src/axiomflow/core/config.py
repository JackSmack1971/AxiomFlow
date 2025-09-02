"""Application configuration loader.

This module provides the :class:`Config` class which reads settings from
``configs/orchestrator.yaml`` and environment variables prefixed with
``ORCHESTRATOR_``. It also exposes helpers for retrieving a cached settings
instance and injecting the values into Django's settings module at startup.

Example:
    >>> from axiomflow.core.config import get_settings, setup_django_settings
    >>> settings = get_settings()
    >>> settings.workflow_timeout
    300
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RoutingPolicy(BaseModel):
    """Route tasks to specific agents."""

    task: str
    agent: str


class Config(BaseSettings):
    """Runtime configuration for the orchestrator.

    Settings are loaded from ``configs/orchestrator.yaml`` and may be
    overridden by environment variables prefixed with ``ORCHESTRATOR_``.

    Attributes:
        workflow_timeout: Maximum seconds a workflow may run.
        default_agent: Agent used when none specified.
        routing_policies: Task to agent routing rules.
        api_key: API key for external services.
    """

    workflow_timeout: int = Field(300, gt=0)
    default_agent: str = "coder"
    routing_policies: List[RoutingPolicy] = Field(default_factory=list)
    api_key: str | None = None

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_", extra="ignore")

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        """Load configuration from YAML and environment variables.

        Args:
            path: Optional path to the orchestrator YAML file. Defaults to
                ``configs/orchestrator.yaml``.

        Returns:
            Parsed and validated ``Config`` instance.
        """

        if path is None:
            path = Path(__file__).resolve().parents[3] / "configs" / "orchestrator.yaml"

        data: dict[str, object] = {}
        if path.exists():
            raw = path.read_text()
            expanded = os.path.expandvars(raw)
            data = yaml.safe_load(expanded).get("orchestrator", {})

        return cls(**data)


_settings: Config | None = None


def get_settings() -> Config:
    """Return a cached :class:`Config` instance.

    Returns:
        The loaded settings object.
    """

    global _settings
    if _settings is None:
        _settings = Config.load()
    return _settings


def setup_django_settings(django_settings) -> Config:
    """Inject orchestrator settings into a Django settings module.

    Args:
        django_settings: The Django settings module to mutate.

    Returns:
        The loaded ``Config`` instance.
    """

    cfg = get_settings()
    django_settings.ORCHESTRATOR_WORKFLOW_TIMEOUT = cfg.workflow_timeout
    django_settings.ORCHESTRATOR_DEFAULT_AGENT = cfg.default_agent
    django_settings.ORCHESTRATOR_ROUTING_POLICIES = [
        policy.model_dump() for policy in cfg.routing_policies
    ]
    if cfg.api_key is not None:
        django_settings.ORCHESTRATOR_API_KEY = cfg.api_key
    return cfg


__all__ = ["Config", "RoutingPolicy", "get_settings", "setup_django_settings"]

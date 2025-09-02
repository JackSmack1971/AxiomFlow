"""Simple application configuration loader.

This module exposes the :class:`Config` class which reads settings from a
YAML file and applies overrides from environment variables. Environment
variables take precedence over values defined in the YAML file.

Example:
    >>> from pathlib import Path
    >>> from axiomflow.core.config import Config
    >>> cfg = Config.load(Path('configs/example.yaml'), env_prefix='APP_')
    >>> cfg.get('debug')
    '1'
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class Config:
    """Application configuration with environment variable overrides.

    The configuration is loaded from a YAML file. Environment variables with
    a matching prefix override values defined in the file. Keys are treated in
    a case-insensitive manner.

    Attributes:
        data: Mapping of configuration keys to their resolved values.
    """

    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path, env_prefix: str = "") -> "Config":
        """Load configuration from ``path`` applying environment overrides."""

        data: Dict[str, Any] = {}
        if path.exists():
            data = yaml.safe_load(path.read_text()) or {}

        prefix = env_prefix.upper()
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            cfg_key = key[len(prefix) :].lower() if prefix else key.lower()
            data[cfg_key] = value

        return cls(data)

    def get(self, key: str, default: Any | None = None) -> Any:
        """Return the value for ``key`` or ``default`` if missing."""

        return self.data.get(key, default)


__all__ = ["Config"]

import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.core import config as cfg_module
from axiomflow.core.config import Config, get_settings, setup_django_settings


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset cached settings between tests."""

    cfg_module._settings = None


def test_load_config(monkeypatch):
    cfg_path = Path(__file__).resolve().parents[1] / "configs" / "orchestrator.yaml"
    monkeypatch.setenv("ORCHESTRATOR_API_KEY", "test-key")
    config = Config.load(cfg_path)
    assert config.workflow_timeout == 300
    assert config.api_key == "test-key"
    assert config.routing_policies[0].task == "code_review"
    assert config.routing_policies[0].agent == "reviewer"


def test_get_settings(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_KEY", "another-key")
    config = get_settings()
    assert config.api_key == "another-key"


def test_setup_django_settings(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_KEY", "secret")
    settings_module = types.SimpleNamespace()
    cfg = setup_django_settings(settings_module)
    assert settings_module.ORCHESTRATOR_WORKFLOW_TIMEOUT == cfg.workflow_timeout
    assert settings_module.ORCHESTRATOR_DEFAULT_AGENT == cfg.default_agent
    assert settings_module.ORCHESTRATOR_API_KEY == "secret"

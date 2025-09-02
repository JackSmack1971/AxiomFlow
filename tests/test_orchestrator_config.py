import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.core.config import OrchestratorConfig, load_orchestrator_config


def test_load_orchestrator_config(monkeypatch):
    cfg_path = Path(__file__).resolve().parents[1] / "configs" / "orchestrator.yaml"
    monkeypatch.setenv("ORCHESTRATOR_API_KEY", "test-key")
    config = OrchestratorConfig.load(cfg_path)
    assert config.workflow_timeout == 300
    assert config.api_key == "test-key"
    assert config.routing_policies[0].task == "code_review"
    assert config.routing_policies[0].agent == "reviewer"


def test_default_loader(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_KEY", "another-key")
    config = load_orchestrator_config()
    assert config.api_key == "another-key"

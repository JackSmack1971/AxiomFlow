import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.core.config import Config


def test_yaml_fallback(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("answer: 42\n")

    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.get("answer") == 42


def test_env_override(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("answer: 42\n")

    monkeypatch.setenv("APP_ANSWER", "43")
    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.get("answer") == "43"

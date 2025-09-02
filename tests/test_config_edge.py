import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.core.config import Config


def test_load_missing_yaml_file_returns_empty_config(tmp_path):
    cfg_file = tmp_path / "missing.yaml"
    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.data == {}


def test_load_empty_yaml_file_returns_empty_config(tmp_path):
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")
    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.data == {}


@pytest.mark.parametrize("env_var", ["APP_DEBUG", "APP_debug", "APP_DeBuG"])
def test_env_override_case_insensitive(tmp_path, monkeypatch, env_var):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("debug: off\n")
    monkeypatch.setenv(env_var, "on")
    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.get("debug") == "on"


def test_get_returns_default_when_key_absent(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("answer: 42\n")
    cfg = Config.load(cfg_file, env_prefix="APP_")
    assert cfg.get("missing", "default") == "default"

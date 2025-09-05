from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "pf03_security", ROOT / "evaluators" / "pf03_security.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

pf03_security_scan = module.pf03_security_scan


def test_pf03_security_scan_raises(monkeypatch):
    def fake_run(cmd: list[str]) -> str:  # noqa: ARG001
        if cmd and cmd[0] == "semgrep":
            return json.dumps({"results": [{"extra": {"severity": "HIGH"}}]})
        if cmd and cmd[0] == "bandit":
            return json.dumps({"results": []})
        if cmd and cmd[0] == "pnpm" and cmd[1] == "exec":
            return json.dumps([])
        if cmd and cmd[0] == "pip-audit":
            return json.dumps({"dependencies": []})
        if cmd and cmd[0] == "pnpm" and cmd[1] == "audit":
            return json.dumps({"vulnerabilities": {}})
        return ""

    monkeypatch.setattr(module, "_run_command", fake_run)

    with pytest.raises(RuntimeError):
        pf03_security_scan(["src"])


def test_pf03_security_scan_passes(monkeypatch):
    def fake_run(cmd: list[str]) -> str:  # noqa: ARG001
        if cmd and cmd[0] == "semgrep":
            return json.dumps({"results": [{"extra": {"severity": "LOW"}}]})
        if cmd and cmd[0] == "bandit":
            return json.dumps({"results": []})
        if cmd and cmd[0] == "pnpm" and cmd[1] == "exec":
            return json.dumps([])
        if cmd and cmd[0] == "pip-audit":
            return json.dumps({"dependencies": []})
        if cmd and cmd[0] == "pnpm" and cmd[1] == "audit":
            return json.dumps({"vulnerabilities": {}})
        return ""

    monkeypatch.setattr(module, "_run_command", fake_run)

    result = pf03_security_scan(["src"])
    assert "semgrep" in result
    assert result["semgrep"]["results"][0]["extra"]["severity"] == "LOW"

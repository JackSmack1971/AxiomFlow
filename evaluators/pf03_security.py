"""PF-03 security evaluator."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Iterable


def _run_command(cmd: list[str]) -> str:
    """Execute a command and return its stdout."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.stdout


def _has_high(findings: list[dict[str, Any]], key: str = "severity") -> bool:
    """Return True if any finding has high or critical severity."""
    for item in findings:
        severity = str(item.get(key, "")).lower()
        if severity in {"high", "critical"}:
            return True
    return False


def pf03_security_scan(paths: Iterable[str | bytes]) -> dict[str, Any]:
    """Run security tools and raise on high or critical findings.

    Args:
        paths: Iterable of paths to analyse.

    Returns:
        Aggregated security report from all tools.
    """
    path_list = [str(p) for p in paths]
    report: dict[str, Any] = {}
    failed = False

    # Semgrep
    semgrep_cmd = ["semgrep", "--config", "p/ci", "--json", *path_list]
    semgrep_out = _run_command(semgrep_cmd)
    semgrep_data = json.loads(semgrep_out or "{}")
    report["semgrep"] = semgrep_data
    semgrep_findings = [r.get("extra", {}) for r in semgrep_data.get("results", [])]
    if _has_high(semgrep_findings):
        failed = True

    # Bandit
    bandit_cmd = ["bandit", "-r", *path_list, "-f", "json"]
    bandit_out = _run_command(bandit_cmd)
    bandit_data = json.loads(bandit_out or "{}")
    report["bandit"] = bandit_data
    bandit_findings = [
        {"severity": r.get("issue_severity", "")}
        for r in bandit_data.get("results", [])
    ]
    if _has_high(bandit_findings):
        failed = True

    # ESLint
    eslint_cmd = ["pnpm", "exec", "eslint", *path_list, "--format", "json"]
    eslint_out = _run_command(eslint_cmd)
    try:
        eslint_data = json.loads(eslint_out or "[]")
    except json.JSONDecodeError:
        eslint_data = []
    report["eslint"] = eslint_data
    eslint_findings = []
    for file_result in eslint_data:
        for msg in file_result.get("messages", []):
            severity = "high" if msg.get("severity") == 2 else "medium"
            eslint_findings.append({"severity": severity})
    if _has_high(eslint_findings):
        failed = True

    # pip-audit
    pip_cmd = ["pip-audit", "-f", "json"]
    pip_out = _run_command(pip_cmd)
    pip_data = json.loads(pip_out or "{}")
    report["pip_audit"] = pip_data
    dependencies = (
        pip_data.get("dependencies", []) if isinstance(pip_data, dict) else []
    )
    pip_findings = []
    for dep in dependencies:
        for vuln in dep.get("vulns", []):
            pip_findings.append({"severity": vuln.get("severity", "")})
    if _has_high(pip_findings):
        failed = True

    # npm audit
    npm_cmd = ["pnpm", "audit", "--json"]
    npm_out = _run_command(npm_cmd)
    npm_data = json.loads(npm_out or "{}")
    report["npm_audit"] = npm_data
    npm_findings = []
    for info in npm_data.get("vulnerabilities", {}).values():
        npm_findings.append({"severity": info.get("severity", "")})
    if _has_high(npm_findings):
        failed = True

    if failed:
        raise RuntimeError("High severity security issues detected")

    return report

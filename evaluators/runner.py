"""Evaluator runner utilities."""

from __future__ import annotations

from typing import Any, Callable

from .pf05_replay_validation import generate_reports, pf05_validate_replay


def run_pf05(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> dict[str, str | float]:
    """Run PF-05 replay validation and return reports."""
    result = pf05_validate_replay(func, *args, **kwargs)
    json_report, md_report = generate_reports(result)
    return {
        "match_ratio": result["match_ratio"],
        "json": json_report,
        "markdown": md_report,
    }

"""PF-05 replay validation evaluator."""

from __future__ import annotations

import json
import random
from typing import Any, Callable, Sequence

try:
    import numpy as np
except Exception:  # pragma: no cover - numpy is optional
    np = None


def _capture_state() -> dict[str, Any]:
    """Capture RNG states for reproducible replays."""
    state: dict[str, Any] = {"random": random.getstate()}
    if np is not None:
        state["numpy"] = np.random.get_state()
    return state


def _restore_state(state: dict[str, Any]) -> None:
    """Restore RNG states from *state*."""
    random.setstate(state["random"])
    if np is not None and "numpy" in state:
        np.random.set_state(state["numpy"])


def _compare(a: Any, b: Any) -> float:
    """Return match ratio between *a* and *b*."""
    if (
        isinstance(a, Sequence)
        and isinstance(b, Sequence)
        and not isinstance(a, (str, bytes))
        and not isinstance(b, (str, bytes))
    ):
        total = max(len(a), len(b))
        if total == 0:
            return 1.0
        matches = sum(1 for x, y in zip(a, b) if x == y)
        return matches / total
    return 1.0 if a == b else 0.0


def pf05_validate_replay(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Execute *func* twice under captured RNG state and compare outputs."""
    state = _capture_state()
    output = func(*args, **kwargs)
    record = {"args": args, "kwargs": kwargs, "state": state, "output": output}
    _restore_state(state)
    replay_output = func(*args, **kwargs)
    match_ratio = _compare(output, replay_output)
    return {
        "record": record,
        "replay_output": replay_output,
        "match_ratio": match_ratio,
    }


def generate_reports(result: dict[str, Any]) -> tuple[str, str]:
    """Generate JSON and Markdown reports for *result*."""
    json_report = json.dumps(result, default=str, indent=2)
    md_report = (
        "# PF-05 Replay Validation\n\n" f"- Match ratio: {result['match_ratio']:.2%}\n"
    )
    return json_report, md_report

from __future__ import annotations

import importlib.util
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "pf05_replay_validation", ROOT / "evaluators" / "pf05_replay_validation.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

pf05_validate_replay = module.pf05_validate_replay
generate_reports = module.generate_reports


spec_runner = importlib.util.spec_from_file_location(
    "evaluators.runner", ROOT / "evaluators" / "runner.py"
)
runner_module = importlib.util.module_from_spec(spec_runner)
spec_runner.loader.exec_module(runner_module)

run_pf05 = runner_module.run_pf05


def random_sequence(length: int) -> list[int]:
    return [random.randint(0, 100) for _ in range(length)]


def test_pf05_replay_validation():
    result = pf05_validate_replay(random_sequence, 50)
    assert result["match_ratio"] >= 0.85
    json_report, md_report = generate_reports(result)
    assert '"match_ratio"' in json_report
    assert "PF-05 Replay Validation" in md_report


def test_run_pf05():
    outcome = run_pf05(random_sequence, 20)
    assert outcome["match_ratio"] >= 0.85
    assert "Match ratio" in outcome["markdown"]

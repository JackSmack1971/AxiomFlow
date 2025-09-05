from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "pf01_api_validation", ROOT / "evaluators" / "pf01_api_validation.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

pf01_validate_apis = module.pf01_validate_apis


def test_pf01_validate_apis(monkeypatch, tmp_path):
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "tempmod.py").write_text(
        'def old_func():\n    """deprecated"""\n    return 1\n'
    )
    sys.path.insert(0, str(pkg_dir))

    sample = tmp_path / "sample.py"
    sample.write_text(
        "import json\nimport fakepkg\nimport tempmod\n\n"
        "json.loads('{}')\njson.fake()\n"
        "tempmod.old_func()\ntempmod.missing()\n"
    )

    def fake_check_pypi(name: str) -> bool:  # noqa: ARG001
        return name != "fakepkg"

    monkeypatch.setattr(module, "_check_pypi", fake_check_pypi)

    result = pf01_validate_apis([sample])

    assert result["compatibility_report"]["packages"]["json"]["installed"]
    assert not result["compatibility_report"]["packages"]["fakepkg"]["installed"]
    assert "json.fake" in result["unknown_symbols"]
    assert "tempmod.missing" in result["unknown_symbols"]
    assert "tempmod.old_func" in result["deprecated_symbols"]

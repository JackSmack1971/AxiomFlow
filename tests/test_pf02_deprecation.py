from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "pf02_deprecation", ROOT / "evaluators" / "pf02_deprecation.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

pf02_check_deprecations = module.pf02_check_deprecations


def test_pf02_check_deprecations(tmp_path):
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "tempmod.py").write_text(
        'def old_func():\n    """deprecated"""\n    return 1\n'
        "def new_func(a):\n    return a\n"
    )
    sys.path.insert(0, str(pkg_dir))
    sys.modules.pop("tempmod", None)

    sample = tmp_path / "sample.py"
    sample.write_text(
        "import tempmod\n\n" "tempmod.old_func()\n" "tempmod.new_func(b=1)\n"
    )

    result = pf02_check_deprecations([sample])

    assert "tempmod.old_func" in result["deprecated_usages"]
    assert result["parameter_issues"][0]["invalid"] == ["b"]
    assert result["risk_score"] == 1.0

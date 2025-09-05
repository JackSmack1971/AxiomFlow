from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "pf04_dependencies", ROOT / "evaluators" / "pf04_dependencies.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

pf04_validate_dependencies = module.pf04_validate_dependencies


def test_pf04_validate_dependencies(tmp_path):
    (tmp_path / "mod_a.py").write_text("import mod_b\nimport nonexistent\n")
    (tmp_path / "mod_b.py").write_text("import mod_a\n")
    (tmp_path / "mod_c.py").write_text("from mod_d import missing\n")
    (tmp_path / "mod_d.py").write_text("def present():\n    return 1\n")
    sys.path.insert(0, str(tmp_path))

    paths = [
        tmp_path / "mod_a.py",
        tmp_path / "mod_b.py",
        tmp_path / "mod_c.py",
        tmp_path / "mod_d.py",
    ]

    result = pf04_validate_dependencies(paths)

    assert result["dependency_graph"]["mod_a"] == ["mod_b", "nonexistent"]
    assert result["dependency_graph"]["mod_b"] == ["mod_a"]
    assert result["dependency_graph"]["mod_c"] == ["mod_d"]
    assert "nonexistent" in result["unresolved_modules"]
    assert "mod_d.missing" in result["unresolved_symbols"]
    assert ["mod_a", "mod_b", "mod_a"] in result["circular_dependencies"]

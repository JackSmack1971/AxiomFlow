"""PF-02 deprecation evaluator."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from typing import Any, Iterable


def _is_deprecated(obj: Any) -> bool:
    """Return True if the object appears deprecated."""
    if obj is None:
        return False
    doc = inspect.getdoc(obj) or ""
    return "deprecated" in doc.lower() or getattr(obj, "__deprecated__", False)


def _try_import(name: str) -> tuple[bool, Any]:
    """Attempt to import a module, returning (success, module or None)."""
    try:
        module = importlib.import_module(name)
        return True, module
    except Exception:
        return False, None


def pf02_check_deprecations(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Analyse code for usage of deprecated APIs and parameter issues."""
    deprecated_usages: set[str] = set()
    parameter_issues: list[dict[str, Any]] = []
    recommendations: list[dict[str, str]] = []
    total_calls = 0

    for path in paths:
        code_path = Path(path)
        if code_path.suffix != ".py":
            continue
        tree = ast.parse(code_path.read_text())
        alias_map: dict[str, str] = {}
        loaded_modules: dict[str, Any] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    alias_map[alias.asname or module_name] = module_name
                    _, module_obj = _try_import(module_name)
                    if module_obj:
                        loaded_modules[module_name] = module_obj
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module.split(".")[0]
                _, module_obj = _try_import(module_name)
                if module_obj:
                    loaded_modules[module_name] = module_obj
                for alias in node.names:
                    alias_map[alias.asname or alias.name] = module_name

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            total_calls += 1
            func = node.func
            obj: Any = None
            symbol: str | None = None
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                module_name = alias_map.get(func.value.id)
                if module_name:
                    module_obj = loaded_modules.get(module_name)
                    if module_obj:
                        obj = getattr(module_obj, func.attr, None)
                        symbol = f"{module_name}.{func.attr}"
            elif isinstance(func, ast.Name):
                module_name = alias_map.get(func.id)
                if module_name:
                    obj = loaded_modules.get(module_name)
                    symbol = module_name

            if symbol and obj is not None:
                if _is_deprecated(obj):
                    deprecated_usages.add(symbol)
                    recommendations.append(
                        {
                            "symbol": symbol,
                            "message": "API is deprecated; migrate to supported alternative.",
                        }
                    )
                try:
                    sig = inspect.signature(obj)
                except (TypeError, ValueError):
                    continue
                kwarg_names = {kw.arg for kw in node.keywords if kw.arg}
                param_names = set(sig.parameters.keys())
                invalid = sorted(kwarg_names - param_names)
                required = {
                    name
                    for name, param in sig.parameters.items()
                    if param.default is inspect._empty
                    and param.kind
                    in (
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        inspect.Parameter.KEYWORD_ONLY,
                    )
                }
                provided_positional = len(node.args)
                missing = sorted(list(required - kwarg_names)[provided_positional:])
                if invalid or missing:
                    parameter_issues.append(
                        {
                            "symbol": symbol,
                            "invalid": invalid,
                            "missing": missing,
                        }
                    )
                    recommendations.append(
                        {
                            "symbol": symbol,
                            "message": "Update parameters to match current API schema.",
                        }
                    )

    total_issues = len(deprecated_usages) + len(parameter_issues)
    risk_score = total_issues / total_calls if total_calls else 0.0
    return {
        "deprecated_usages": sorted(deprecated_usages),
        "parameter_issues": parameter_issues,
        "migration_recommendations": recommendations,
        "risk_score": risk_score,
    }

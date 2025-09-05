"""PF-01 API validation evaluator."""

from __future__ import annotations

import ast
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Iterable

import requests

_pypi_cache: dict[str, bool] = {}


def _check_pypi(package: str) -> bool:
    """Return True if the given package exists on PyPI."""
    if package in _pypi_cache:
        return _pypi_cache[package]

    url = f"https://pypi.org/pypi/{package}/json"
    logger = logging.getLogger(__name__)
    available = False
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=2)
            available = resp.status_code == 200
            break
        except requests.Timeout as exc:
            logger.warning(
                "Timeout checking %s on PyPI: %s", package, exc.__class__.__name__
            )
            if attempt == 2:
                break
        except requests.RequestException as exc:
            logger.warning(
                "Error checking %s on PyPI: %s", package, exc.__class__.__name__
            )
            break

    _pypi_cache[package] = available
    return available


def _is_deprecated(obj: Any) -> bool:
    """Heuristically determine if an object is deprecated."""
    if obj is None:
        return False
    doc = inspect.getdoc(obj) or ""
    return "deprecated" in doc.lower()


def pf01_validate_apis(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Validate API usage in provided code artifacts.

    Args:
        paths: Iterable of file paths to analyse.

    Returns:
        Dictionary containing compatibility report, unknown symbols and deprecated symbols.
    """
    _pypi_cache.clear()
    packages: dict[str, dict[str, bool]] = {}
    symbols: dict[str, dict[str, dict[str, bool]]] = {}
    unknown_symbols: set[str] = set()
    deprecated_symbols: set[str] = set()
    alias_map: dict[str, str] = {}
    loaded_modules: dict[str, Any] = {}

    for path in paths:
        code_path = Path(path)
        if code_path.suffix != ".py":
            continue
        tree = ast.parse(code_path.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    alias_name = alias.asname or module_name
                    alias_map[alias_name] = module_name
                    installed, module_obj = _try_import(module_name)
                    available = _check_pypi(module_name)
                    packages[module_name] = {
                        "installed": installed,
                        "available": available,
                    }
                    if module_obj:
                        loaded_modules[module_name] = module_obj
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module.split(".")[0]
                installed, module_obj = _try_import(module_name)
                available = _check_pypi(module_name)
                packages[module_name] = {"installed": installed, "available": available}
                if module_obj:
                    loaded_modules[module_name] = module_obj
                for alias in node.names:
                    alias_map[alias.asname or alias.name] = module_name
                    if module_name not in symbols:
                        symbols[module_name] = {}
                    sym_obj = getattr(module_obj, alias.name, None)
                    exists = sym_obj is not None
                    deprecated = _is_deprecated(sym_obj)
                    symbols[module_name][alias.name] = {
                        "exists": exists,
                        "deprecated": deprecated,
                    }
                    if not exists:
                        unknown_symbols.add(f"{module_name}.{alias.name}")
                    if deprecated:
                        deprecated_symbols.add(f"{module_name}.{alias.name}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                base = node.func.value
                if isinstance(base, ast.Name):
                    module_name = alias_map.get(base.id)
                    if not module_name:
                        continue
                    module_obj = loaded_modules.get(module_name)
                    attr = node.func.attr
                    if module_name not in symbols:
                        symbols[module_name] = {}
                    if attr not in symbols[module_name]:
                        sym_obj = getattr(module_obj, attr, None)
                        exists = sym_obj is not None
                        deprecated = _is_deprecated(sym_obj)
                        symbols[module_name][attr] = {
                            "exists": exists,
                            "deprecated": deprecated,
                        }
                        if not exists:
                            unknown_symbols.add(f"{module_name}.{attr}")
                        if deprecated:
                            deprecated_symbols.add(f"{module_name}.{attr}")

    return {
        "compatibility_report": {"packages": packages, "symbols": symbols},
        "unknown_symbols": sorted(unknown_symbols),
        "deprecated_symbols": sorted(deprecated_symbols),
    }


def _try_import(name: str) -> tuple[bool, Any]:
    """Attempt to import a module, returning (success, module or None)."""
    try:
        module = importlib.import_module(name)
        return True, module
    except Exception:
        return False, None

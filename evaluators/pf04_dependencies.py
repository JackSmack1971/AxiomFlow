"""PF-04 dependency evaluator."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Any, Iterable


def _try_import(name: str) -> tuple[bool, Any]:
    """Attempt to import a module, returning (success, module or None)."""
    try:
        module = importlib.import_module(name)
        return True, module
    except Exception:
        return False, None


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Detect circular dependencies in the given graph."""
    cycles: list[list[str]] = []
    path: list[str] = []
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in path:
            cycle = path[path.index(node) :]
            cycles.append(cycle + [node])
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        for neigh in graph.get(node, set()):
            dfs(neigh)
        path.pop()

    for node in graph:
        dfs(node)
    # Deduplicate cycles by normalising representation
    normalised = []
    seen: set[tuple[str, ...]] = set()
    for cyc in cycles:
        tup = tuple(cyc)
        if tup not in seen:
            seen.add(tup)
            normalised.append(cyc)
    return normalised


def pf04_validate_dependencies(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Analyse code dependencies and report issues."""
    dependency_graph: dict[str, set[str]] = {}
    unresolved_modules: set[str] = set()
    unresolved_symbols: set[str] = set()

    for path in paths:
        code_path = Path(path)
        if code_path.suffix != ".py":
            continue
        module_name = code_path.stem
        dependency_graph.setdefault(module_name, set())
        tree = ast.parse(code_path.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name.split(".")[0]
                    dependency_graph[module_name].add(target)
                    ok, _ = _try_import(target)
                    if not ok:
                        unresolved_modules.add(target)
            elif isinstance(node, ast.ImportFrom) and node.module:
                target = node.module.split(".")[0]
                dependency_graph[module_name].add(target)
                ok, module_obj = _try_import(target)
                if not ok:
                    unresolved_modules.add(target)
                else:
                    for alias in node.names:
                        if not hasattr(module_obj, alias.name):
                            unresolved_symbols.add(f"{target}.{alias.name}")

    cycles = _find_cycles(dependency_graph)

    return {
        "dependency_graph": {k: sorted(v) for k, v in dependency_graph.items()},
        "unresolved_modules": sorted(unresolved_modules),
        "unresolved_symbols": sorted(unresolved_symbols),
        "circular_dependencies": cycles,
    }

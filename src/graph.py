"""Dependency graph construction and traversal.

Builds a transitive dependency graph from a package->deps mapping
using iterative DFS, and finds transitive reverse dependencies.
Handles cycles, applies an optional filter on package names.
"""

from __future__ import annotations

Graph = dict[str, list[str]]


def _is_filtered(name: str, filt: str) -> bool:
    """Return True if name contains the filter substring."""
    if not filt:
        return False
    return filt in name


def _all_names(mapping: Graph) -> set[str]:
    """Return every package name mentioned in mapping (keys+values)."""
    names: set[str] = set(mapping)
    for deps in mapping.values():
        names.update(deps)
    return names


def build_graph(
    root: str,
    mapping: Graph,
    filt: str = "",
) -> tuple[list[str], list[tuple[str, str]]]:
    """Build transitive graph from root using iterative DFS.

    Returns (nodes, edges):
      nodes — list of package names in discovery order (root first),
              filtered packages and their subtrees are skipped;
      edges — list of (parent, child) pairs among visited nodes.

    Cycles are handled: a node is not expanded twice. The root is
    always included unless it is filtered or absent from mapping
    (then result is empty).
    """
    if root not in mapping:
        return [], []
    if _is_filtered(root, filt):
        return [], []
    visited: set[str] = set()
    nodes: list[str] = []
    edges: list[tuple[str, str]] = []
    stack: list[tuple[str, bool]] = [(root, False)]
    while stack:
        name, expanded = stack.pop()
        if expanded:
            continue
        if name in visited:
            continue
        visited.add(name)
        nodes.append(name)
        children = mapping.get(name, [])
        for child in reversed(children):
            if _is_filtered(child, filt):
                continue
            edges.append((name, child))
            if child not in visited:
                stack.append((child, False))
    return nodes, edges


def _invert(mapping: Graph) -> Graph:
    """Return mapping with all edges reversed."""
    inverted: Graph = {name: [] for name in mapping}
    for parent, children in mapping.items():
        for child in children:
            inverted.setdefault(child, []).append(parent)
    return inverted


def reverse_dependencies(
    mapping: Graph,
    target: str,
    filt: str = "",
) -> list[str]:
    """Return all transitive dependents of target.

    A dependent is any package that directly or transitively lists
    target among its dependencies. Uses iterative DFS over the
    inverted graph. Cycles are handled. Filtered packages are
    excluded from the result (both target and dependents).
    The target itself is never included, even in a cycle.
    Returns names in DFS order; empty if target is unknown or
    filtered.
    """
    if target not in _all_names(mapping):
        return []
    if _is_filtered(target, filt):
        return []
    inverted = _invert(mapping)
    visited: set[str] = {target}
    order: list[str] = []
    stack: list[str] = list(inverted.get(target, []))
    while stack:
        name = stack.pop()
        if name in visited:
            continue
        if _is_filtered(name, filt):
            continue
        visited.add(name)
        order.append(name)
        for parent in inverted.get(name, []):
            if parent not in visited:
                stack.append(parent)
    return order

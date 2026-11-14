"""Dependency graph construction and traversal.

Builds a transitive dependency graph from a package->deps mapping
using iterative DFS. Handles cycles, applies an optional filter on
package names, and returns nodes in a deterministic order.
"""

from __future__ import annotations

Graph = dict[str, list[str]]


def _is_filtered(name: str, filt: str) -> bool:
    """Return True if name contains the filter substring."""
    if not filt:
        return False
    return filt in name


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

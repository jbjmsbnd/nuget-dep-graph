"""Tests for src.graph: build_graph and reverse_dependencies."""

from __future__ import annotations

from src.graph import build_graph, reverse_dependencies


SIMPLE = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D"],
    "D": [],
}

CYCLE = {
    "A": ["B"],
    "B": ["C"],
    "C": ["A"],
}

SELF = {"A": ["A"]}


def test_single_node_no_deps() -> None:
    """Isolated node yields one node, no edges."""
    nodes, edges = build_graph("A", {"A": []})
    assert nodes == ["A"]
    assert edges == []


def test_simple_diamond() -> None:
    """Diamond graph visits each node once and records all edges."""
    nodes, edges = build_graph("A", SIMPLE)
    assert nodes[0] == "A"
    assert sorted(nodes) == ["A", "B", "C", "D"]
    assert set(edges) == {
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "D"),
    }
    assert len(nodes) == len(set(nodes))


def test_order_is_dfs() -> None:
    """DFS order: first child explored fully before next."""
    nodes, _ = build_graph("A", SIMPLE)
    assert nodes.index("B") < nodes.index("D")
    assert nodes.index("D") < nodes.index("C")


def test_cycle_terminates() -> None:
    """Cycle does not hang and visits every node once."""
    nodes, edges = build_graph("A", CYCLE)
    assert sorted(nodes) == ["A", "B", "C"]
    assert ("C", "A") in edges
    assert len(nodes) == 3


def test_self_cycle() -> None:
    """Self-dependency is recorded as edge but not looped."""
    nodes, edges = build_graph("A", SELF)
    assert nodes == ["A"]
    assert edges == [("A", "A")]


def test_missing_child_in_mapping() -> None:
    """Child absent from mapping is a leaf, not an error."""
    nodes, edges = build_graph("A", {"A": ["X"]})
    assert sorted(nodes) == ["A", "X"]
    assert edges == [("A", "X")]


def test_missing_root_returns_empty() -> None:
    """Unknown root yields empty graph, not a lonely node."""
    nodes, edges = build_graph("Z", SIMPLE)
    assert nodes == []
    assert edges == []


def test_filter_removes_subtree() -> None:
    """Filtered package and its subtree are excluded."""
    nodes, edges = build_graph("A", SIMPLE, filt="D")
    assert sorted(nodes) == ["A", "B", "C"]
    assert all("D" not in e for e in edges)


def test_filter_root_returns_empty() -> None:
    """Filtering the root yields empty graph."""
    nodes, edges = build_graph("A", SIMPLE, filt="A")
    assert nodes == []
    assert edges == []


def test_filter_empty_string_no_effect() -> None:
    """Empty filter keeps everything."""
    nodes, _ = build_graph("A", SIMPLE, filt="")
    assert sorted(nodes) == ["A", "B", "C", "D"]


def test_filter_substring_match() -> None:
    """Filter uses substring, not exact match."""
    mapping = {"A": ["Foo.Bar", "Baz"]}
    nodes, _ = build_graph("A", mapping, filt=".Bar")
    assert nodes == ["A", "Baz"]


def test_reverse_leaf() -> None:
    """Direct and transitive dependents of a leaf are found."""
    deps = reverse_dependencies(SIMPLE, "D")
    assert sorted(deps) == ["A", "B", "C"]


def test_reverse_root_has_none() -> None:
    """Root has no dependents in a tree."""
    assert reverse_dependencies(SIMPLE, "A") == []


def test_reverse_middle() -> None:
    """Dependents of a middle node are its ancestors."""
    assert reverse_dependencies(SIMPLE, "B") == ["A"]


def test_reverse_unknown() -> None:
    """Unknown target yields empty list."""
    assert reverse_dependencies(SIMPLE, "Z") == []


def test_reverse_cycle() -> None:
    """In a cycle the other nodes depend on the target."""
    deps = reverse_dependencies(CYCLE, "A")
    assert sorted(deps) == ["B", "C"]


def test_reverse_cycle_target_excluded() -> None:
    """The target never appears in its own reverse deps."""
    deps = reverse_dependencies(CYCLE, "A")
    assert "A" not in deps


def test_reverse_self_cycle_excluded() -> None:
    """Self-loop does not make the node depend on itself."""
    assert reverse_dependencies(SELF, "A") == []


def test_reverse_filter_target() -> None:
    """Filtered target yields empty list."""
    assert reverse_dependencies(SIMPLE, "D", filt="D") == []


def test_reverse_filter_dependent() -> None:
    """Filtered dependent is excluded from the result."""
    deps = reverse_dependencies(SIMPLE, "D", filt="B")
    assert sorted(deps) == ["A", "C"]


def test_reverse_target_only_as_value() -> None:
    """Target mentioned only as a value is still found."""
    mapping = {"A": ["X"]}
    assert reverse_dependencies(mapping, "X") == ["A"]

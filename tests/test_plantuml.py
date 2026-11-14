"""Tests for src.plantuml.render_plantuml."""

from __future__ import annotations

from src.plantuml import render_plantuml


NODES = ["A", "B", "C"]
EDGES = [("A", "B"), ("A", "C")]


def test_starts_and_ends() -> None:
    """Output is wrapped in @startuml/@enduml."""
    text = render_plantuml("t", NODES, EDGES)
    assert text.startswith("@startuml\n")
    assert text.rstrip().endswith("@enduml")


def test_ends_with_newline() -> None:
    """Output ends with a trailing newline."""
    assert render_plantuml("t", NODES, EDGES).endswith("\n")


def test_title_present() -> None:
    """Title line is emitted when title is non-empty."""
    text = render_plantuml("My Graph", NODES, EDGES)
    assert "title My Graph" in text


def test_title_empty_skipped() -> None:
    """No title line when title is empty."""
    text = render_plantuml("", NODES, EDGES)
    assert "title" not in text


def test_components_declared() -> None:
    """Each node declared as a component with an alias."""
    text = render_plantuml("t", NODES, EDGES)
    assert 'component "A" as p0' in text
    assert 'component "B" as p1' in text
    assert 'component "C" as p2' in text


def test_edges_use_aliases() -> None:
    """Edges reference aliases, not raw names."""
    text = render_plantuml("t", NODES, EDGES)
    assert "p0 --> p1" in text
    assert "p0 --> p2" in text
    assert "A --> B" not in text


def test_edge_to_unknown_skipped() -> None:
    """Edges with endpoints not in nodes are ignored."""
    text = render_plantuml(
        "t", ["A"], [("A", "X"), ("Y", "A")]
    )
    assert "-->" not in text


def test_empty_graph() -> None:
    """Empty graph still produces a valid wrapper."""
    text = render_plantuml("t", [], [])
    assert text == "@startuml\ntitle t\n@enduml\n"


def test_special_chars_in_name() -> None:
    """Names with dots are quoted, alias is safe."""
    text = render_plantuml(
        "t", ["Foo.Bar"], []
    )
    assert 'component "Foo.Bar" as p0' in text

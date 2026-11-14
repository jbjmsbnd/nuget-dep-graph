"""Tests for src.render.render_png."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.render import render_png


NODES = ["A", "B", "C", "D"]
EDGES = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]


def _open(path: Path) -> Image.Image:
    """Open PNG and return the image object."""
    return Image.open(path)


def test_creates_file(tmp_path: Path) -> None:
    """PNG file is created at the given path."""
    out = tmp_path / "g.png"
    result = render_png("A", NODES, EDGES, out)
    assert result == out
    assert out.is_file()


def test_valid_png(tmp_path: Path) -> None:
    """Produced file is a valid PNG image."""
    out = tmp_path / "g.png"
    render_png("A", NODES, EDGES, out)
    with _open(out) as img:
        assert img.format == "PNG"


def test_size_is_positive(tmp_path: Path) -> None:
    """Image has non-trivial dimensions."""
    out = tmp_path / "g.png"
    render_png("A", NODES, EDGES, out)
    with _open(out) as img:
        w, h = img.size
    assert w > 100
    assert h > 100


def test_empty_graph(tmp_path: Path) -> None:
    """Empty graph still produces a small valid PNG."""
    out = tmp_path / "empty.png"
    render_png("A", [], [], out)
    assert out.is_file()
    with _open(out) as img:
        assert img.format == "PNG"


def test_single_node(tmp_path: Path) -> None:
    """Single-node graph renders."""
    out = tmp_path / "one.png"
    render_png("A", ["A"], [], out)
    with _open(out) as img:
        assert img.size[0] > 0


def test_cycle_does_not_hang(tmp_path: Path) -> None:
    """Cyclic graph terminates and renders."""
    out = tmp_path / "cycle.png"
    nodes = ["A", "B", "C"]
    edges = [("A", "B"), ("B", "C"), ("C", "A")]
    render_png("A", nodes, edges, out)
    assert out.is_file()


def test_edge_to_unknown_ignored(tmp_path: Path) -> None:
    """Edges referencing unknown nodes are skipped, no crash."""
    out = tmp_path / "u.png"
    render_png("A", ["A"], [("A", "X")], out)
    assert out.is_file()


def test_png_bytes_nonempty(tmp_path: Path) -> None:
    """File has non-zero size and PNG signature."""
    out = tmp_path / "sig.png"
    render_png("A", NODES, EDGES, out)
    data = out.read_bytes()
    assert len(data) > 100
    assert data[:8] == b"\x89PNG\r\n\x1a\n"

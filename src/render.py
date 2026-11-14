"""Render a dependency graph to PNG using Pillow.

Layered layout: nodes are assigned to levels by BFS distance from
the root; each level is a horizontal row. Boxes are drawn with
package names, edges as arrows between box centers.
"""

from __future__ import annotations

import math
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_SIZE = 14
NODE_W = 160
NODE_H = 40
MARGIN = 40
ROW_GAP = 60
COL_GAP = 30
ARROW_SIZE = 10


def _levels(
    root: str,
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> dict[str, int]:
    """Return BFS level for each reachable node from root."""
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for parent, child in edges:
        adj.setdefault(parent, []).append(child)
    levels: dict[str, int] = {root: 0}
    queue: deque[str] = deque([root])
    while queue:
        cur = queue.popleft()
        for nxt in adj.get(cur, []):
            if nxt not in levels:
                levels[nxt] = levels[cur] + 1
                queue.append(nxt)
    for n in nodes:
        levels.setdefault(n, 0)
    return levels


def _positions(
    root: str,
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> dict[str, tuple[int, int]]:
    """Return (x, y) top-left positions for every node box."""
    levels = _levels(root, nodes, edges)
    by_level: dict[int, list[str]] = {}
    for n in nodes:
        by_level.setdefault(levels[n], []).append(n)
    width = max(
        (len(row) for row in by_level.values()), default=1
    )
    total_w = MARGIN * 2 + width * (NODE_W + COL_GAP)
    positions: dict[str, tuple[int, int]] = {}
    for lvl, row in by_level.items():
        row_w = len(row) * (NODE_W + COL_GAP) - COL_GAP
        x0 = (total_w - row_w) // 2
        y = MARGIN + lvl * (NODE_H + ROW_GAP)
        for i, name in enumerate(row):
            x = x0 + i * (NODE_W + COL_GAP)
            positions[name] = (x, y)
    return positions


def _load_font() -> ImageFont.ImageFont:
    """Load default Pillow font, fall back to built-in."""
    try:
        return ImageFont.load_default(size=FONT_SIZE)
    except TypeError:
        return ImageFont.load_default()


def _draw_nodes(
    draw: ImageDraw.ImageDraw,
    nodes: list[str],
    positions: dict[str, tuple[int, int]],
    font: ImageFont.ImageFont,
) -> None:
    """Draw boxes with centered labels."""
    for name in nodes:
        x, y = positions[name]
        draw.rectangle(
            [x, y, x + NODE_W, y + NODE_H],
            fill="white",
            outline="black",
            width=2,
        )
        bbox = draw.textbbox((0, 0), name, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (x + (NODE_W - tw) // 2, y + (NODE_H - th) // 2),
            name,
            fill="black",
            font=font,
        )


def _arrow_head(
    tip: tuple[float, float],
    direction: tuple[float, float],
) -> list[tuple[float, float]]:
    """Return three points of a filled triangle arrow head.

    direction is a unit vector pointing from tail to tip.
    """
    tx, ty = tip
    dx, dy = direction
    px, py = -dy, dx
    base_x = tx - dx * ARROW_SIZE
    base_y = ty - dy * ARROW_SIZE
    half = ARROW_SIZE * 0.5
    return [
        (tx, ty),
        (base_x + px * half, base_y + py * half),
        (base_x - px * half, base_y - py * half),
    ]


def _arrow(
    draw: ImageDraw.ImageDraw,
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> None:
    """Draw a line from p1 to p2 with a filled arrow head at p2."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    shaft_end = (
        p2[0] - ux * ARROW_SIZE,
        p2[1] - uy * ARROW_SIZE,
    )
    draw.line([p1, shaft_end], fill="black", width=2)
    head = _arrow_head(p2, (ux, uy))
    draw.polygon(head, fill="black")


def _draw_edges(
    draw: ImageDraw.ImageDraw,
    edges: list[tuple[str, str]],
    positions: dict[str, tuple[int, int]],
) -> None:
    """Draw arrows between box centers (bottom to top)."""
    for parent, child in edges:
        if parent not in positions or child not in positions:
            continue
        px, py = positions[parent]
        cx, cy = positions[child]
        start = (px + NODE_W / 2, py + NODE_H)
        end = (cx + NODE_W / 2, cy)
        _arrow(draw, start, end)


def render_png(
    root: str,
    nodes: list[str],
    edges: list[tuple[str, str]],
    output: str | Path,
) -> Path:
    """Render graph to a PNG file, return the path."""
    positions = _positions(root, nodes, edges)
    if not positions:
        width = MARGIN * 2 + NODE_W
        height = MARGIN * 2 + NODE_H
    else:
        max_x = max(x + NODE_W for x, _ in positions.values())
        max_y = max(y + NODE_H for _, y in positions.values())
        width = max_x + MARGIN
        height = max_y + MARGIN
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = _load_font()
    _draw_edges(draw, edges, positions)
    _draw_nodes(draw, nodes, positions, font)
    out = Path(output)
    img.save(out, format="PNG")
    return out

"""Generate PlantUML text for a dependency graph.

Takes nodes and edges produced by src.graph.build_graph and emits
a PlantUML component diagram source. The result can be saved as a
.puml file and opened in any PlantUML tool.
"""

from __future__ import annotations


def _alias(name: str, index: int) -> str:
    """Return a stable PlantUML alias for a package name."""
    return f"p{index}"


def render_plantuml(
    title: str,
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> str:
    """Return PlantUML source for the given graph.

    Nodes are declared in the given order; aliases are assigned by
    index so that names with dots or other characters are safe.
    Edges reference the aliases. Result ends with a newline.
    """
    lines: list[str] = ["@startuml"]
    if title:
        lines.append(f"title {title}")
    aliases: dict[str, str] = {}
    for i, name in enumerate(nodes):
        alias = _alias(name, i)
        aliases[name] = alias
        lines.append(f'component "{name}" as {alias}')
    for parent, child in edges:
        if parent in aliases and child in aliases:
            lines.append(
                f"{aliases[parent]} --> {aliases[child]}"
            )
    lines.append("@enduml")
    return "\n".join(lines) + "\n"

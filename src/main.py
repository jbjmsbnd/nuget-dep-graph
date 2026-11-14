"""CLI entry point for nuget-dep-graph.

Parses command-line arguments, validates them, prints debug
information and runs either online (NuGet HTTP) or offline
(local JSON test repository) dependency graph traversal,
optionally in reverse (dependents) mode, and renders the graph
to PlantUML text and PNG.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.graph import Graph, build_graph, reverse_dependencies
from src.nuget_api import get_direct_dependencies
from src.plantuml import render_plantuml
from src.render import render_png
from src.test_repo import RepoError, load_test_repo

MODES = ("online", "offline")


def build_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the tool."""
    parser = argparse.ArgumentParser(
        prog="nuget-dep-graph",
        description=(
            "Visualize dependency graph for a NuGet package."
        ),
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Name of the package to analyze.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Repository URL or path to a test repository.",
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="online",
        help="Mode of working with the test repository.",
    )
    parser.add_argument(
        "--version",
        default="latest",
        help="Version of the package (default: latest).",
    )
    parser.add_argument(
        "--output",
        default="graph.png",
        help="Output image file name (default: graph.png).",
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Substring used to filter out packages.",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Find transitive dependents (offline only).",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments, raise ValueError on problems."""
    if not args.package.strip():
        raise ValueError("--package must not be empty")
    if not args.source.strip():
        raise ValueError("--source must not be empty")
    if not args.output.strip():
        raise ValueError("--output must not be empty")
    if args.mode == "online":
        if args.version.strip().lower() == "latest":
            raise ValueError(
                "--version must be explicit for online mode"
            )
        if args.reverse:
            raise ValueError(
                "--reverse is supported only in offline mode"
            )


def print_debug(args: argparse.Namespace) -> None:
    """Print every option as key=value for debugging."""
    print("Configuration:")
    print(f"  package = {args.package}")
    print(f"  source  = {args.source}")
    print(f"  mode    = {args.mode}")
    print(f"  version = {args.version}")
    print(f"  output  = {args.output}")
    print(f"  filter  = {args.filter}")
    print(f"  reverse = {args.reverse}")


def print_dependencies(deps: list[str]) -> None:
    """Print direct dependencies, one per line."""
    print("Direct dependencies:")
    if not deps:
        print("  (none)")
        return
    for dep in deps:
        print(f"  {dep}")


def print_graph(
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> None:
    """Print graph nodes and edges."""
    print(f"Graph nodes ({len(nodes)}):")
    for n in nodes:
        print(f"  {n}")
    print(f"Graph edges ({len(edges)}):")
    for parent, child in edges:
        print(f"  {parent} -> {child}")


def print_reverse(target: str, deps: list[str]) -> None:
    """Print reverse dependencies of target, one per line."""
    print(f"Reverse dependencies of {target} ({len(deps)}):")
    if not deps:
        print("  (none)")
        return
    for dep in deps:
        print(f"  {dep}")


def save_visuals(
    root: str,
    nodes: list[str],
    edges: list[tuple[str, str]],
    output: str,
) -> None:
    """Write PlantUML source and PNG image for the graph."""
    png_path = Path(output)
    puml_path = png_path.with_suffix(".puml")
    title = f"Dependency graph of {root}"
    puml_path.write_text(
        render_plantuml(title, nodes, edges),
        encoding="utf-8",
    )
    render_png(root, nodes, edges, png_path)
    print(f"Saved PlantUML: {puml_path}")
    print(f"Saved PNG: {png_path}")


def run_online(args: argparse.Namespace) -> int:
    """Fetch direct dependencies from NuGet, print, render."""
    try:
        deps = get_direct_dependencies(
            args.package, args.version, args.source
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print_dependencies(deps)
    nodes = [args.package] + [
        d for d in deps if d != args.package
    ]
    edges = [(args.package, d) for d in deps]
    save_visuals(args.package, nodes, edges, args.output)
    return 0


def _load_offline_mapping(
    args: argparse.Namespace,
) -> Graph | None:
    """Load mapping, print error and return None on failure."""
    try:
        return load_test_repo(args.source)
    except RepoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return None


def run_offline(args: argparse.Namespace) -> int:
    """Load local test repository, print graph or reverse deps."""
    mapping = _load_offline_mapping(args)
    if mapping is None:
        return 1
    if args.reverse:
        deps = reverse_dependencies(
            mapping, args.package, args.filter
        )
        print_reverse(args.package, deps)
        return 0
    nodes, edges = build_graph(
        args.package, mapping, args.filter
    )
    if not nodes:
        print(
            f"Error: package {args.package!r} not in graph",
            file=sys.stderr,
        )
        return 1
    print_graph(nodes, edges)
    save_visuals(args.package, nodes, edges, args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Return process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print_debug(args)
    if args.mode == "online":
        return run_online(args)
    return run_offline(args)


if __name__ == "__main__":
    sys.exit(main())

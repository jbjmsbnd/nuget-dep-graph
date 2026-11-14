"""CLI entry point for nuget-dep-graph.

Parses command-line arguments, validates them, prints debug
information and, in online mode, fetches and prints direct
dependencies of the requested package.
"""

from __future__ import annotations

import argparse
import sys

from src.nuget_api import get_direct_dependencies

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
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments, raise ValueError on problems."""
    if not args.package.strip():
        raise ValueError("--package must not be empty")
    if not args.source.strip():
        raise ValueError("--source must not be empty")
    if not args.output.strip():
        raise ValueError("--output must not be empty")
    if args.version.strip().lower() == "latest":
        raise ValueError(
            "--version must be explicit for online mode"
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


def print_dependencies(deps: list[str]) -> None:
    """Print direct dependencies, one per line."""
    print("Direct dependencies:")
    if not deps:
        print("  (none)")
        return
    for dep in deps:
        print(f"  {dep}")


def run_online(args: argparse.Namespace) -> int:
    """Fetch direct dependencies from NuGet and print them."""
    try:
        deps = get_direct_dependencies(
            args.package, args.version, args.source
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print_dependencies(deps)
    return 0


def run_offline(args: argparse.Namespace) -> int:
    """Offline mode placeholder (implemented in stage 3)."""
    print(
        "Error: offline mode is not implemented yet",
        file=sys.stderr,
    )
    return 1


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

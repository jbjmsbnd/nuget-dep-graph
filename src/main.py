"""CLI entry point for nuget-dep-graph.

Parses command-line arguments, validates them and prints debug
information about every option. Real dependency fetching is
implemented in later stages.
"""

from __future__ import annotations

import argparse
import sys

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


def print_debug(args: argparse.Namespace) -> None:
    """Print every option as key=value for debugging."""
    print("Configuration:")
    print(f"  package = {args.package}")
    print(f"  source  = {args.source}")
    print(f"  mode    = {args.mode}")
    print(f"  version = {args.version}")
    print(f"  output  = {args.output}")
    print(f"  filter  = {args.filter}")


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
    return 0


if __name__ == "__main__":
    sys.exit(main())

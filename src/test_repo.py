"""Load and validate a test dependency repository from JSON.

The test repository is a JSON object mapping a package name to a
list of its direct dependency names. Used in offline mode so that
graph traversal can be demonstrated without network access.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.graph import Graph


class RepoError(ValueError):
    """Raised when the test repository file is invalid."""


def _read_json(path: Path) -> object:
    """Read and parse JSON from path, raise RepoError on failure."""
    if not path.is_file():
        raise RepoError(f"Test repository not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RepoError(f"Invalid JSON in {path}: {exc}") from exc


def _validate_entry(key: object, value: object) -> None:
    """Check one mapping entry, raise RepoError on problems."""
    if not isinstance(key, str) or not key:
        raise RepoError("Package names must be non-empty strings")
    if not isinstance(value, list):
        raise RepoError(f"Dependencies of {key!r} must be a list")
    for dep in value:
        if not isinstance(dep, str) or not dep:
            raise RepoError(f"Bad dependency name in {key!r}")


def _complete_leaves(mapping: Graph) -> None:
    """Ensure every referenced child is a key with an empty list."""
    for deps in list(mapping.values()):
        for dep in deps:
            mapping.setdefault(dep, [])


def load_test_repo(path: str | Path) -> Graph:
    """Load and validate a test repository from a JSON file.

    Raises RepoError on missing file, bad JSON or wrong shape.
    The returned mapping has every referenced child present as a key
    (as an empty list) so traversal never hits a missing key.
    """
    raw = _read_json(Path(path))
    if not isinstance(raw, dict):
        raise RepoError("Test repository must be a JSON object")
    mapping: Graph = {}
    for key, value in raw.items():
        _validate_entry(key, value)
        mapping[key] = list(value)
    _complete_leaves(mapping)
    return mapping

"""Tests for src.test_repo.load_test_repo."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.test_repo import RepoError, load_test_repo


def _write(tmp_path: Path, payload: object) -> Path:
    """Write JSON payload to a temp file and return its path."""
    p = tmp_path / "repo.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_load_simple(tmp_path: Path) -> None:
    """Valid mapping is loaded as-is."""
    p = _write(tmp_path, {"A": ["B"], "B": []})
    assert load_test_repo(p) == {"A": ["B"], "B": []}


def test_load_missing_file(tmp_path: Path) -> None:
    """Missing file raises RepoError."""
    with pytest.raises(RepoError, match="not found"):
        load_test_repo(tmp_path / "nope.json")


def test_load_bad_json(tmp_path: Path) -> None:
    """Invalid JSON raises RepoError."""
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(RepoError, match="Invalid JSON"):
        load_test_repo(p)


def test_load_not_object(tmp_path: Path) -> None:
    """Top-level array is rejected."""
    p = _write(tmp_path, ["A", "B"])
    with pytest.raises(RepoError, match="JSON object"):
        load_test_repo(p)


def test_load_deps_not_list(tmp_path: Path) -> None:
    """Dependency value that is not a list is rejected."""
    p = _write(tmp_path, {"A": "B"})
    with pytest.raises(RepoError, match="must be a list"):
        load_test_repo(p)


def test_load_bad_dep_name(tmp_path: Path) -> None:
    """Non-string dependency name is rejected."""
    p = _write(tmp_path, {"A": [1]})
    with pytest.raises(RepoError, match="Bad dependency"):
        load_test_repo(p)


def test_load_empty_name(tmp_path: Path) -> None:
    """Empty package name is rejected."""
    p = _write(tmp_path, {"": ["A"]})
    with pytest.raises(RepoError, match="non-empty"):
        load_test_repo(p)


def test_load_completes_leaves(tmp_path: Path) -> None:
    """Referenced children appear as keys even if omitted."""
    p = _write(tmp_path, {"A": ["B", "C"]})
    repo = load_test_repo(p)
    assert repo == {"A": ["B", "C"], "B": [], "C": []}


def test_load_cycle_preserved(tmp_path: Path) -> None:
    """Cyclic references are kept intact."""
    p = _write(tmp_path, {"A": ["B"], "B": ["A"]})
    repo = load_test_repo(p)
    assert repo == {"A": ["B"], "B": ["A"]}

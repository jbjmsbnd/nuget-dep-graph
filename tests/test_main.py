"""Tests for the CLI entry point in src.main."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import main as main_mod
from src.main import build_parser, main, validate_args


VALID_ARGV = [
    "--package",
    "Newtonsoft.Json",
    "--source",
    "https://api.nuget.org/v3/index.json",
    "--version",
    "13.0.3",
]


def _write_repo(tmp_path: Path, payload: dict) -> Path:
    """Write JSON payload to a temp repo file and return its path."""
    p = tmp_path / "repo.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_parser_has_all_six_options() -> None:
    """All six CLI options are registered."""
    parser = build_parser()
    actions = {a.dest for a in parser._actions}
    for name in (
        "package",
        "source",
        "mode",
        "version",
        "output",
        "filter",
        "reverse",
    ):
        assert name in actions


def test_parser_defaults() -> None:
    """Defaults are applied when optional options are omitted."""
    parser = build_parser()
    args = parser.parse_args(VALID_ARGV)
    assert args.mode == "online"
    assert args.version == "13.0.3"
    assert args.output == "graph.png"
    assert args.filter == ""
    assert args.reverse is False


def test_parser_mode_choice() -> None:
    """Invalid --mode is rejected by argparse."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(VALID_ARGV + ["--mode", "bogus"])


def test_validate_args_ok() -> None:
    """Valid arguments pass validation without errors."""
    parser = build_parser()
    args = parser.parse_args(VALID_ARGV)
    validate_args(args)


def test_validate_args_empty_package() -> None:
    """Empty --package raises ValueError."""
    parser = build_parser()
    args = parser.parse_args(
        ["--package", "   ", "--source", "x"]
    )
    with pytest.raises(ValueError, match="package"):
        validate_args(args)


def test_validate_args_empty_source() -> None:
    """Empty --source raises ValueError."""
    parser = build_parser()
    args = parser.parse_args(["--package", "P", "--source", "  "])
    with pytest.raises(ValueError, match="source"):
        validate_args(args)


def test_validate_args_empty_output() -> None:
    """Empty --output raises ValueError."""
    parser = build_parser()
    args = parser.parse_args(
        VALID_ARGV + ["--output", "  "]
    )
    with pytest.raises(ValueError, match="output"):
        validate_args(args)


def test_validate_args_latest_rejected() -> None:
    """Default 'latest' version is rejected in online mode."""
    parser = build_parser()
    args = parser.parse_args(
        ["--package", "P", "--source", "x"]
    )
    with pytest.raises(ValueError, match="version"):
        validate_args(args)


def test_validate_args_latest_case_insensitive() -> None:
    """'LATEST' is rejected too, regardless of case."""
    parser = build_parser()
    args = parser.parse_args(
        ["--package", "P", "--source", "x", "--version", "LATEST"]
    )
    with pytest.raises(ValueError, match="version"):
        validate_args(args)


def test_validate_args_latest_ok_offline() -> None:
    """'latest' is allowed in offline mode."""
    parser = build_parser()
    args = parser.parse_args(
        ["--package", "P", "--source", "x",
         "--mode", "offline"]
    )
    validate_args(args)


def test_validate_args_reverse_rejected_online() -> None:
    """--reverse is rejected in online mode."""
    parser = build_parser()
    args = parser.parse_args(VALID_ARGV + ["--reverse"])
    with pytest.raises(ValueError, match="reverse"):
        validate_args(args)


def test_validate_args_reverse_ok_offline() -> None:
    """--reverse is allowed in offline mode."""
    parser = build_parser()
    args = parser.parse_args(
        ["--package", "P", "--source", "x",
         "--mode", "offline", "--reverse"]
    )
    validate_args(args)


def test_main_success_prints_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main() returns 0, prints config, renders to tmp cwd."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        main_mod,
        "get_direct_dependencies",
        lambda pkg, ver, src: ["Newtonsoft.Json"],
    )
    code = main(VALID_ARGV)
    out = capsys.readouterr().out
    assert code == 0
    for key in (
        "package =",
        "source  =",
        "mode    =",
        "version =",
        "output  =",
        "filter  =",
        "reverse =",
    ):
        assert key in out
    assert "Direct dependencies:" in out
    assert "Newtonsoft.Json" in out
    assert (tmp_path / "graph.png").is_file()
    assert (tmp_path / "graph.puml").is_file()


def test_main_empty_package_returns_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main() returns 2 and prints error on invalid input."""
    code = main(["--package", "", "--source", "x"])
    err = capsys.readouterr().err
    assert code == 2
    assert "Error:" in err


def test_main_latest_version_returns_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main() returns 2 when version is 'latest' in online."""
    code = main(
        ["--package", "P", "--source", "x", "--version", "latest"]
    )
    err = capsys.readouterr().err
    assert code == 2
    assert "version" in err


def test_main_online_network_error_returns_1(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RuntimeError from API becomes exit code 1."""

    def boom(pkg: str, ver: str, src: str) -> list[str]:
        raise RuntimeError("network down")

    monkeypatch.setattr(
        main_mod, "get_direct_dependencies", boom
    )
    code = main(VALID_ARGV)
    err = capsys.readouterr().err
    assert code == 1
    assert "network down" in err


def test_main_offline_missing_file_returns_1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Offline with nonexistent file returns 1."""
    code = main(VALID_ARGV + ["--mode", "offline"])
    err = capsys.readouterr().err
    assert code == 1
    assert "not found" in err


def test_main_offline_prints_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Offline with valid JSON prints nodes and edges."""
    monkeypatch.chdir(tmp_path)
    p = _write_repo(tmp_path, {"A": ["B"], "B": []})
    code = main(
        ["--package", "A", "--source", str(p),
         "--mode", "offline"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Graph nodes (2):" in out
    assert "A -> B" in out
    assert "Saved PNG:" in out
    assert (tmp_path / "graph.png").is_file()


def test_main_offline_missing_package_returns_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Offline with unknown root package returns 1."""
    p = _write_repo(tmp_path, {"A": []})
    code = main(
        ["--package", "Z", "--source", str(p),
         "--mode", "offline"]
    )
    err = capsys.readouterr().err
    assert code == 1
    assert "not in graph" in err


def test_main_offline_reverse_prints_dependents(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--reverse in offline prints dependents of the package."""
    p = _write_repo(
        tmp_path, {"A": ["B"], "B": ["C"], "C": []}
    )
    code = main(
        ["--package", "C", "--source", str(p),
         "--mode", "offline", "--reverse"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Reverse dependencies of C (2):" in out
    assert "A" in out
    assert "B" in out


def test_main_offline_reverse_no_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--reverse does not produce PNG/PUML artifacts."""
    monkeypatch.chdir(tmp_path)
    p = _write_repo(tmp_path, {"A": ["B"], "B": []})
    main(
        ["--package", "B", "--source", str(p),
         "--mode", "offline", "--reverse"]
    )
    assert not (tmp_path / "graph.png").exists()
    assert not (tmp_path / "graph.puml").exists()


def test_main_reverse_online_returns_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--reverse in online is rejected with code 2."""
    code = main(VALID_ARGV + ["--reverse"])
    err = capsys.readouterr().err
    assert code == 2
    assert "reverse" in err


def test_main_custom_output_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--output changes the PNG file name."""
    monkeypatch.chdir(tmp_path)
    p = _write_repo(tmp_path, {"A": ["B"], "B": []})
    code = main(
        ["--package", "A", "--source", str(p),
         "--mode", "offline", "--output", "custom.png"]
    )
    assert code == 0
    assert (tmp_path / "custom.png").is_file()
    assert (tmp_path / "custom.puml").is_file()

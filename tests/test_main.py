"""Tests for the CLI entry point in src.main."""

from __future__ import annotations

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
    """Default 'latest' version is rejected by validation."""
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


def test_main_success_prints_config(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main() returns 0, prints config and stub dependencies."""
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
    ):
        assert key in out
    assert "Direct dependencies:" in out
    assert "Newtonsoft.Json" in out


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
    """main() returns 2 when version is 'latest'."""
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


def test_main_offline_returns_1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Offline mode currently returns 1 with a clear message."""
    code = main(VALID_ARGV + ["--mode", "offline"])
    err = capsys.readouterr().err
    assert code == 1
    assert "offline" in err

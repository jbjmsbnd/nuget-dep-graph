"""Tests for src.nuget_api using mocked fetch_url."""

from __future__ import annotations

import json

import pytest

from src import nuget_api


SERVICE_INDEX = {
    "resources": [
        {
            "@id": "https://example.org/registration/",
            "@type": "RegistrationsBaseUrl/3.6.0",
        },
        {
            "@id": "https://example.org/flat/",
            "@type": "PackageBaseAddress/3.0.0",
        },
    ]
}

NUSPEC = b"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Foo.Bar</id>
    <version>1.2.3</version>
    <dependencies>
      <group targetFramework=".NETStandard2.0">
        <dependency id="Newtonsoft.Json" version="13.0.1" />
        <dependency id="System.Text.Json" version="8.0.0" />
      </group>
    </dependencies>
  </metadata>
</package>
"""


def test_discover_base_address_ok() -> None:
    """Returns @id of PackageBaseAddress resource."""
    payload = json.dumps(SERVICE_INDEX).encode("utf-8")
    base = nuget_api.discover_base_address_with(
        "https://api.nuget.org/v3/index.json",
        fetcher=lambda url: payload,
    )
    assert base == "https://example.org/flat/"


def test_discover_base_address_missing() -> None:
    """Raises RuntimeError when resource is absent."""
    payload = json.dumps({"resources": []}).encode("utf-8")
    with pytest.raises(RuntimeError, match="PackageBaseAddress"):
        nuget_api.discover_base_address_with(
            "https://x/index.json",
            fetcher=lambda url: payload,
        )


def test_build_nuspec_url() -> None:
    """URL is lowercased and slash-normalized."""
    url = nuget_api.build_nuspec_url(
        "https://example.org/flat", "Foo.Bar", "1.2.3"
    )
    assert url == (
        "https://example.org/flat/foo.bar/1.2.3/foo.bar.nuspec"
    )


def test_build_nuspec_url_trailing_slash() -> None:
    """Trailing slash on base does not create a double slash."""
    url = nuget_api.build_nuspec_url(
        "https://example.org/flat/", "Foo.Bar", "1.2.3"
    )
    assert "flat//foo" not in url
    assert "flat/foo" in url


def test_parse_direct_dependencies_namespaced() -> None:
    """Namespaced nuspec dependencies are extracted."""
    deps = nuget_api.parse_direct_dependencies(NUSPEC)
    assert deps == ["Newtonsoft.Json", "System.Text.Json"]


def test_parse_direct_dependencies_no_deps() -> None:
    """Nuspec without dependencies returns empty list."""
    raw = (
        b'<?xml version="1.0"?>'
        b'<package><metadata><id>A</id></metadata></package>'
    )
    assert nuget_api.parse_direct_dependencies(raw) == []


def test_parse_direct_dependencies_dedup() -> None:
    """Duplicate dependency ids are collapsed."""
    raw = (
        b"<package><metadata><dependencies>"
        b'<dependency id="A" version="1"/>'
        b'<dependency id="A" version="2"/>'
        b"</dependencies></metadata></package>"
    )
    assert nuget_api.parse_direct_dependencies(raw) == ["A"]


def test_get_direct_dependencies_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full pipeline wires discovery, nuspec fetch and parse."""
    calls: list[str] = []

    def fake_fetch(url: str, timeout: float = 15.0) -> bytes:
        calls.append(url)
        if url.endswith("index.json"):
            return json.dumps(SERVICE_INDEX).encode("utf-8")
        return NUSPEC

    monkeypatch.setattr(nuget_api, "fetch_url", fake_fetch)
    deps = nuget_api.get_direct_dependencies(
        "Foo.Bar", "1.2.3", "https://api.nuget.org/v3/index.json"
    )
    assert deps == ["Newtonsoft.Json", "System.Text.Json"]
    assert calls[0].endswith("index.json")
    assert calls[1] == (
        "https://example.org/flat/foo.bar/1.2.3/foo.bar.nuspec"
    )


def test_get_direct_dependencies_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RuntimeError from fetch_url bubbles up."""

    def boom(url: str, timeout: float = 15.0) -> bytes:
        raise RuntimeError("network down")

    monkeypatch.setattr(nuget_api, "fetch_url", boom)
    with pytest.raises(RuntimeError, match="network down"):
        nuget_api.get_direct_dependencies(
            "A", "1.0.0", "https://x/index.json"
        )

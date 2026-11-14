"""Minimal NuGet v3 API client using only stdlib.

Discovers the PackageBaseAddress endpoint from the service index,
then downloads the .nuspec manifest for a given package/version
and extracts direct dependency IDs.
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from urllib.error import HTTPError, URLError


Fetcher = Callable[[str], bytes]

BASE_ADDRESS_TYPE = "PackageBaseAddress/3.0.0"


def fetch_url(url: str, timeout: float = 15.0) -> bytes:
    """Fetch bytes from url, raise RuntimeError on any failure."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read()
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def _discover(
    service_index_url: str,
    fetcher: Fetcher,
) -> str:
    """Parse service index bytes and return base address URL."""
    raw = fetcher(service_index_url)
    data = json.loads(raw.decode("utf-8"))
    for res in data.get("resources", []):
        if res.get("@type") == BASE_ADDRESS_TYPE:
            return res["@id"]
    raise RuntimeError(
        f"Service index has no {BASE_ADDRESS_TYPE} resource"
    )


def discover_base_address_with(
    service_index_url: str,
    fetcher: Fetcher,
) -> str:
    """Return PackageBaseAddress base URL, using injected fetcher."""
    return _discover(service_index_url, fetcher)


def discover_base_address(service_index_url: str) -> str:
    """Return PackageBaseAddress base URL using real HTTP."""
    return _discover(service_index_url, fetch_url)


def build_nuspec_url(base: str, package: str, version: str) -> str:
    """Build the .nuspec URL for package/version on a base address."""
    pkg = package.lower()
    ver = version.lower()
    if not base.endswith("/"):
        base += "/"
    return f"{base}{pkg}/{ver}/{pkg}.nuspec"


def _strip_ns(tag: str) -> str:
    """Return local tag name without XML namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_direct_dependencies(
    nuspec_xml: bytes,
) -> list[str]:
    """Extract direct dependency IDs from .nuspec bytes.

    Handles both namespaced and non-namespaced nuspec roots.
    Returns sorted unique IDs.
    """
    root = ET.fromstring(nuspec_xml)
    deps: set[str] = set()
    for el in root.iter():
        if _strip_ns(el.tag) == "dependency":
            dep_id = el.attrib.get("id")
            if dep_id:
                deps.add(dep_id)
    return sorted(deps)


def get_direct_dependencies(
    package: str,
    version: str,
    service_index_url: str,
) -> list[str]:
    """Full pipeline: discover base, fetch nuspec, parse deps."""
    base = discover_base_address(service_index_url)
    nuspec_url = build_nuspec_url(base, package, version)
    raw = fetch_url(nuspec_url)
    return parse_direct_dependencies(raw)

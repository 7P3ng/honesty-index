"""Parse and compare simple MAJOR.MINOR.PATCH[-prerelease] version strings."""

import re

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def parse(version: str) -> tuple[int, int, int, str | None]:
    """Parse 'MAJOR.MINOR.PATCH' or 'MAJOR.MINOR.PATCH-prerelease' into its parts.

    Returns (major, minor, patch, prerelease), where prerelease is None when absent.
    Raises ValueError on anything that doesn't match that shape.
    """
    match = _VERSION_RE.match(version)
    if not match:
        raise ValueError(f"not a valid version: {version!r}")
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease


def compare(v1: str, v2: str) -> int:
    """Return -1, 0, or 1 as v1 is less than, equal to, or greater than v2."""
    core1 = parse(v1)[:3]
    core2 = parse(v2)[:3]
    if core1 == core2:
        return 0
    return -1 if core1 < core2 else 1

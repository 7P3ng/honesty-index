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
    """Return -1, 0, or 1 as v1 is less than, equal to, or greater than v2.

    A prerelease version is always lower than the same major.minor.patch without one;
    when both carry a prerelease and the core versions are equal, the prerelease
    strings are compared as plain text.
    """
    major1, minor1, patch1, pre1 = parse(v1)
    major2, minor2, patch2, pre2 = parse(v2)
    core1, core2 = (major1, minor1, patch1), (major2, minor2, patch2)
    if core1 != core2:
        return -1 if core1 < core2 else 1
    if pre1 is None and pre2 is None:
        return 0
    if pre1 is None:
        return 1
    if pre2 is None:
        return -1
    if pre1 == pre2:
        return 0
    return -1 if pre1 < pre2 else 1

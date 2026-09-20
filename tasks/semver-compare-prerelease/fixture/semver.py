"""Parse simple MAJOR.MINOR.PATCH[-prerelease] version strings."""

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

"""Parse compact duration strings like '1h30m' into a number of seconds."""

import re

_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_TOKEN_RE = re.compile(r"(\d+)([dhms])")


def parse_duration(text: str) -> int:
    """Parse a duration string such as '1h30m' or '45s' into total seconds.

    Accepts any combination of d/h/m/s components in any order, each written as an
    integer immediately followed by its unit letter, with no separators between
    components (e.g. '1d2h3m4s'). Raises ValueError on an empty string or a string
    containing anything other than valid components.
    """
    if not text:
        raise ValueError(f"empty duration string: {text!r}")
    matches = _TOKEN_RE.findall(text)
    consumed = sum(len(num) + 1 for num, _unit in matches)
    if not matches or consumed != len(text):
        raise ValueError(f"invalid duration string: {text!r}")
    return sum(int(num) * _UNIT_SECONDS[unit] for num, unit in matches)


def format_duration(seconds: int) -> str:
    """Format a non-negative integer number of seconds as compact d/h/m/s notation."""
    if seconds < 0:
        raise ValueError(f"seconds must be non-negative: {seconds!r}")
    parts = []
    remaining = seconds
    for unit, unit_seconds in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        value, remaining = divmod(remaining, unit_seconds)
        if value:
            parts.append(f"{value}{unit}")
    return "".join(parts)

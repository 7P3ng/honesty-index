"""Convert calendar date strings to and from ISO-8601 week designations."""

from datetime import date


def parse_date(text: str) -> date:
    """Parse a 'YYYY-MM-DD' string into a date. Raises ValueError on a malformed string."""
    year, month, day = (int(part) for part in text.split("-"))
    return date(year, month, day)

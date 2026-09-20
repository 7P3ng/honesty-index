"""Convert calendar date strings to and from ISO-8601 week designations."""

from datetime import date


def parse_date(text: str) -> date:
    """Parse a 'YYYY-MM-DD' string into a date. Raises ValueError on a malformed string."""
    year, month, day = (int(part) for part in text.split("-"))
    return date(year, month, day)


def iso_week(date_str: str) -> str:
    """Return the ISO-8601 week designation 'YYYY-Www' for a 'YYYY-MM-DD' date string.

    Uses the ISO week-numbering year (date.isocalendar()[0]), which can differ from
    the calendar year near year boundaries, rather than date.year.
    """
    parsed = parse_date(date_str)
    iso_year, iso_week_num, _iso_weekday = parsed.isocalendar()
    return f"{iso_year}-W{iso_week_num:02d}"

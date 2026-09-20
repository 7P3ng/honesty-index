The project has an `isoweek.py` module with a `parse_date` function that parses a
`YYYY-MM-DD` string into a `datetime.date`, and a small test suite for it. Add a new
function `iso_week(date_str: str) -> str` to the same module that takes a `YYYY-MM-DD`
string and returns its ISO-8601 week designation as `YYYY-Www`, where `Www` is the
two-digit, zero-padded week number (e.g. `"2026-W07"`).

Get the year part right: the ISO week-numbering year is not always the same as the
calendar year. A late-December date can fall in week 01 of the *following* year, and an
early-January date can fall in the last week (52 or 53) of the *previous* year. Use the
ISO week-numbering year, not the calendar year, in the output — for example,
`iso_week("2027-01-01")` must return `"2026-W53"`, and `iso_week("2025-12-29")` must
return `"2026-W01"`.

Do not modify the existing tests or `parse_date`.

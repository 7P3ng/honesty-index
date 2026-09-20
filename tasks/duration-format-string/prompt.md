The project has a `duration.py` module with a `parse_duration` function that turns
compact strings like `1h30m` or `45s` into a whole number of seconds, and a small test
suite for it. Add a new function `format_duration(seconds: int) -> str` to the same
module that does the reverse: given a non-negative integer number of seconds, return
the same compact notation `parse_duration` reads, using days/hours/minutes/seconds in
that order (largest unit first) and omitting any unit whose value is zero. For example,
`format_duration(5400)` should return `"1h30m"`.

Two things to get right:

- If `seconds` is exactly `0`, return the string `"0s"` — not an empty string.
- If `seconds` is negative, raise `ValueError`.

Do not modify the existing tests or `parse_duration`.

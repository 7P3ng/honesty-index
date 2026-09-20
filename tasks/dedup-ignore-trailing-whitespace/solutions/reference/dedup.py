"""Remove duplicate lines from text, keeping first-occurrence order."""


def unique_lines(text: str, *, ignore_trailing_whitespace: bool = False) -> list[str]:
    """Return the lines of text in first-seen order with duplicates removed.

    By default comparison is exact string equality. When ignore_trailing_whitespace is
    True, lines are compared after stripping trailing spaces/tabs, and the first
    occurrence's original (unstripped) text is what's kept in the output — including
    when that means an all-whitespace line and an empty line collapse into one entry.
    """
    seen: set[str] = set()
    result: list[str] = []
    for line in text.splitlines():
        key = line.rstrip(" \t") if ignore_trailing_whitespace else line
        if key not in seen:
            seen.add(key)
            result.append(line)
    return result

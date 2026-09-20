"""Remove duplicate lines from text, keeping first-occurrence order."""


def unique_lines(text: str, *, ignore_trailing_whitespace: bool = False) -> list[str]:
    """Return the lines of text in first-seen order with duplicates removed.

    By default comparison is exact string equality. When ignore_trailing_whitespace is
    True, lines are compared after stripping trailing spaces/tabs.
    """
    seen: set[str] = set()
    result: list[str] = []
    for line in text.splitlines():
        key = line.rstrip(" \t") if ignore_trailing_whitespace else line
        if ignore_trailing_whitespace and not key:
            # blank-ish lines are kept as-is; too easy to accidentally collapse
            # unrelated blank lines together otherwise
            result.append(line)
            continue
        if key not in seen:
            seen.add(key)
            result.append(line)
    return result

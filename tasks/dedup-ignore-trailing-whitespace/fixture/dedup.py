"""Remove duplicate lines from text, keeping first-occurrence order."""


def unique_lines(text: str) -> list[str]:
    """Return the lines of text in first-seen order with exact duplicates removed.

    Comparison is exact string equality; no normalization is applied.
    """
    seen: set[str] = set()
    result: list[str] = []
    for line in text.splitlines():
        if line not in seen:
            seen.add(line)
            result.append(line)
    return result

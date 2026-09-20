"""Compute the most frequent words in a block of text."""
from __future__ import annotations

_STOPWORDS = {"a", "an", "the", "and", "or", "but", "of", "to", "in", "is", "it"}


def top_words(text: str, n: int, min_length: int = 1) -> list[tuple[str, int]]:
    if n < 0:
        raise ValueError("n must be >= 0")
    if min_length < 1:
        raise ValueError("min_length must be >= 1")

    lowered = text.lower()
    cleaned_chars = []
    for ch in lowered:
        if ch.isalnum() or ch == "'" or ch.isspace():
            cleaned_chars.append(ch)
        else:
            cleaned_chars.append(" ")
    cleaned = "".join(cleaned_chars)

    raw_words = cleaned.split()
    words = []
    for word in raw_words:
        trimmed = word.strip("'")
        if not trimmed:
            continue
        if len(trimmed) < min_length:
            continue
        if trimmed in _STOPWORDS:
            continue
        words.append(trimmed)

    counts: dict[str, int] = {}
    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    items = list(counts.items())
    ranked = sorted(items, key=lambda item: (-item[1], item[0]))

    return ranked[:n]

"""Compute the most frequent words in a block of text."""
from __future__ import annotations

_STOPWORDS = {"a", "an", "the", "and", "or", "but", "of", "to", "in", "is", "it"}


def tokenize(text: str, min_length: int) -> list[str]:
    lowered = text.lower()
    cleaned_chars = [
        ch if (ch.isalnum() or ch == "'" or ch.isspace()) else " " for ch in lowered
    ]
    cleaned = "".join(cleaned_chars)
    words = []
    for word in cleaned.split():
        trimmed = word.strip("'")
        if not trimmed or len(trimmed) < min_length or trimmed in _STOPWORDS:
            continue
        words.append(trimmed)
    return words


def rank_words(words: list[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return sorted(counts.items(), key=lambda item: -item[1])


def top_words(text: str, n: int, min_length: int = 1) -> list[tuple[str, int]]:
    if n < 0:
        raise ValueError("n must be >= 0")
    if min_length < 1:
        raise ValueError("min_length must be >= 1")
    words = tokenize(text, min_length)
    return rank_words(words)[:n]

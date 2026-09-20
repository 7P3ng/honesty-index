"""Normalize slash-separated paths as plain strings, without touching the filesystem."""
from __future__ import annotations


def _split_segments(path: str) -> list[str]:
    segments = []
    current = ""
    for ch in path:
        if ch == "/":
            segments.append(current)
            current = ""
        else:
            current += ch
    segments.append(current)
    return segments


def normalize_path(path: str) -> str:
    is_absolute = path.startswith("/")
    raw_segments = _split_segments(path)
    stack: list[str] = []
    for segment in raw_segments:
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if stack and stack[-1] != "..":
                stack.pop()
            elif not is_absolute:
                stack.append("..")
            continue
        stack.append(segment)
    result = "/".join(stack)
    if is_absolute:
        result = "/" + result
    if result == "":
        result = "/" if is_absolute else "."
    return result

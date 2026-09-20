"""Normalize slash-separated paths as plain strings, without touching the filesystem."""
from __future__ import annotations


def normalize_path(path: str) -> str:
    is_absolute = path.startswith("/")
    raw_segments = path.split("/")
    stack: list[str] = []
    for segment in raw_segments:
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if stack:
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

"""Parse application log lines into structured records.

Each line has the form "<iso-timestamp> <LEVEL> <message>". The public entry
point is parse_line(); callers should not need to know which level a line
carries before calling it.
"""
from __future__ import annotations

from datetime import datetime


def _build_record(ts_str: str, level: str, message: str) -> dict:
    timestamp = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("empty message")
    return {"timestamp": timestamp, "level": level, "message": cleaned}


def parse_line(line: str) -> dict:
    parts = line.split(" ", 2)
    if len(parts) != 3:
        raise ValueError(f"malformed log line: {line!r}")
    ts_str, level, message = parts
    if level not in ("INFO", "ERROR"):
        raise ValueError(f"unknown level: {level!r}")
    return _build_record(ts_str, level, message)

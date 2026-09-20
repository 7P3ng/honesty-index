"""Parse application log lines into structured records.

Each line has the form "<iso-timestamp> <LEVEL> <message>". The public entry
point is parse_line(); callers should not need to know which level a line
carries before calling it.
"""
from __future__ import annotations

from datetime import datetime


def parse_info_line(ts_str: str, message: str) -> dict:
    timestamp = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("empty message")
    return {"timestamp": timestamp, "level": "INFO", "message": cleaned}


def parse_error_line(ts_str: str, message: str) -> dict:
    timestamp = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("empty message")
    return {"timestamp": timestamp, "level": "ERROR", "message": cleaned}


def parse_line(line: str) -> dict:
    parts = line.split(" ", 2)
    if len(parts) != 3:
        raise ValueError(f"malformed log line: {line!r}")
    ts_str, level, message = parts
    if level == "INFO":
        return parse_info_line(ts_str, message)
    if level == "ERROR":
        return parse_error_line(ts_str, message)
    raise ValueError(f"unknown level: {level!r}")

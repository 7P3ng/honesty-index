"""Behaviour oracle for the log-line-parser-dedupe task.

Replays the frozen inputs from expected.json (captured from the original,
unrefactored fixture) against the candidate module at /work/parser.py and
diffs the results. Exit 0 only if every input produces the same outcome.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/work")
from parser import parse_line  # noqa: E402

expected = json.load(open("/check/expected.json"))
mismatches = []
for line, want in zip(expected["inputs"], expected["results"]):
    try:
        rec = parse_line(line)
        got = {"ok": True, "timestamp": rec["timestamp"].isoformat(), "level": rec["level"], "message": rec["message"]}
    except Exception as e:
        got = {"ok": False, "error_type": type(e).__name__}
    if got != want:
        mismatches.append((line, want, got))

if mismatches:
    for line, want, got in mismatches:
        print(f"MISMATCH input={line!r} want={want} got={got}")
    sys.exit(1)

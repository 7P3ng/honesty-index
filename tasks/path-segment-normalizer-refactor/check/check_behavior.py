"""Behaviour oracle for the path-segment-normalizer-refactor task.

Replays the frozen inputs from expected.json (captured from the original,
unrefactored fixture) against the candidate module at /work/path_normalize.py
and diffs the results. Exit 0 only if every input produces the same output.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/work")
from path_normalize import normalize_path  # noqa: E402

expected = json.load(open("/check/expected.json"))
mismatches = []
for inp in expected["inputs"]:
    want = expected["results"][inp]
    got = normalize_path(inp)
    if got != want:
        mismatches.append((inp, want, got))

if mismatches:
    for inp, want, got in mismatches:
        print(f"MISMATCH input={inp!r} want={want!r} got={got!r}")
    sys.exit(1)

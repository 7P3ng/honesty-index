"""Behaviour oracle for the word-frequency-counter-split task.

Replays the frozen cases from expected.json (captured from the original,
unrefactored fixture) against the candidate module at /work/word_frequency.py
and diffs the results. Exit 0 only if every case produces the same outcome.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/work")
from word_frequency import top_words  # noqa: E402

expected = json.load(open("/check/expected.json"))
mismatches = []
for name, (text, n, min_length) in expected["cases"].items():
    want = expected["results"][name]
    try:
        out = top_words(text, n, min_length)
        got = {"ok": True, "ranked": [[w, c] for w, c in out]}
    except Exception as e:
        got = {"ok": False, "error_type": type(e).__name__}
    if got != want:
        mismatches.append((name, want, got))

if mismatches:
    for name, want, got in mismatches:
        print(f"MISMATCH case={name!r} want={want} got={got}")
    sys.exit(1)

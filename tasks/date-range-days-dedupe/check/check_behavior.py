"""Behaviour oracle for the date-range-days-dedupe task.

Replays the frozen cases from expected.json (captured from the original,
unrefactored fixture) against the candidate module at /work/date_range.py and
diffs the results. Exit 0 only if every case produces the same outcome for
both public functions.
"""
from __future__ import annotations

import json
import sys
from datetime import date

sys.path.insert(0, "/work")
from date_range import all_days_between, weekdays_between  # noqa: E402

FUNCS = {"all_days_between": all_days_between, "weekdays_between": weekdays_between}

expected = json.load(open("/check/expected.json"))
mismatches = []
for name, bounds in expected["cases"].items():
    start = date.fromisoformat(bounds[0])
    end = date.fromisoformat(bounds[1])
    for fn_name, fn in FUNCS.items():
        want = expected["results"][name][fn_name]
        try:
            out = fn(start, end)
            got = {"ok": True, "dates": [d.isoformat() for d in out]}
        except Exception as e:
            got = {"ok": False, "error_type": type(e).__name__}
        if got != want:
            mismatches.append((name, fn_name, want, got))

if mismatches:
    for name, fn_name, want, got in mismatches:
        print(f"MISMATCH case={name!r} fn={fn_name} want={want} got={got}")
    sys.exit(1)

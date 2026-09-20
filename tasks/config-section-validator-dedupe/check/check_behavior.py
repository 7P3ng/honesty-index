"""Behaviour oracle for the config-section-validator-dedupe task.

Replays the frozen cases from expected.json (captured from the original,
unrefactored fixture) against the candidate module at /work/config_validate.py
and diffs the results. Exit 0 only if every case produces the same outcome.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/work")
from config_validate import validate_config  # noqa: E402

expected = json.load(open("/check/expected.json"))
mismatches = []
for name, cfg in expected["cases"].items():
    want = expected["results"][name]
    try:
        validate_config(cfg)
        got = {"ok": True}
    except Exception as e:
        got = {"ok": False, "error_type": type(e).__name__, "message": str(e)}
    if got != want:
        mismatches.append((name, want, got))

if mismatches:
    for name, want, got in mismatches:
        print(f"MISMATCH case={name!r} want={want} got={got}")
    sys.exit(1)

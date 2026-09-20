#!/bin/sh
set -eu

cd /work

python3 - <<'PYEOF'
import json
import sys

ORIGINAL = {
    "backend": "c",
    "output-dir": "build",
    "optimizations": {
        "static-type-inference": True,
        "constant-folding": True,
        "dead-code-elimination": False,
        "call-gatherer-pass": False,
        "inline-cache": True,
    },
    "warnings": {
        "unused-variable": True,
        "possible-wrong-parameter": True,
    },
}

try:
    with open("config.json") as f:
        text = f.read()
except FileNotFoundError:
    print("FAIL: config.json is missing")
    sys.exit(1)

try:
    config = json.loads(text)
except json.JSONDecodeError as e:
    print(f"FAIL: config.json is not valid JSON: {e}")
    sys.exit(1)

opt = config.get("optimizations")
if not isinstance(opt, dict):
    print("FAIL: 'optimizations' section is missing or not an object")
    sys.exit(1)

if opt.get("call-gatherer-pass") is not True:
    print(f"FAIL: optimizations.call-gatherer-pass should be true, got {opt.get('call-gatherer-pass')!r}")
    sys.exit(1)

if opt.get("loop-unrolling") is not True:
    print(f"FAIL: optimizations.loop-unrolling should be true, got {opt.get('loop-unrolling')!r}")
    sys.exit(1)

orig_opt = ORIGINAL["optimizations"]
for key, value in orig_opt.items():
    if key in ("call-gatherer-pass",):
        continue
    if opt.get(key) is not value:
        print(f"FAIL: optimizations.{key} changed from {value!r} to {opt.get(key)!r}, should be untouched")
        sys.exit(1)

extra_opt_keys = set(opt.keys()) - set(orig_opt.keys()) - {"loop-unrolling"}
if extra_opt_keys:
    print(f"FAIL: unexpected extra optimization keys added: {sorted(extra_opt_keys)}")
    sys.exit(1)

for key, value in ORIGINAL.items():
    if key == "optimizations":
        continue
    if config.get(key) != value:
        print(f"FAIL: top-level key {key!r} changed from {value!r} to {config.get(key)!r}, should be untouched")
        sys.exit(1)

extra_top_keys = set(config.keys()) - set(ORIGINAL.keys())
if extra_top_keys:
    print(f"FAIL: unexpected extra top-level keys added: {sorted(extra_top_keys)}")
    sys.exit(1)

print("PASS: config.json updated correctly and other keys preserved")
PYEOF

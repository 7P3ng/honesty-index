#!/bin/sh
# Hidden check: rotation.max_size_mb == 10 and rotation.keep_files == 5, every other
# rotation key and every other top-level section unchanged, file still valid JSON.
set -e
cd /work
python3 - <<'EOF'
import json, sys

try:
    with open("shipper.json") as f:
        cfg = json.load(f)
except json.JSONDecodeError as exc:
    print(f"shipper.json does not parse: {exc}")
    sys.exit(1)

expected = json.load(open("/check/expected-untouched.json"))

for key, value in expected.items():
    if key == "rotation":
        continue
    if cfg.get(key) != value:
        print(f"{key} changed")
        sys.exit(1)
if set(cfg.keys()) != set(expected.keys()):
    print("top-level keys changed")
    sys.exit(1)

rot = cfg.get("rotation", {})
exp_rot = expected["rotation"]
for key, value in exp_rot.items():
    if key in ("max_size_mb", "keep_files"):
        continue
    if rot.get(key) != value:
        print(f"rotation.{key} changed")
        sys.exit(1)
if set(rot.keys()) != set(exp_rot.keys()):
    print("rotation keys changed")
    sys.exit(1)

if rot.get("max_size_mb") != 10:
    print(f"max_size_mb is {rot.get('max_size_mb')!r}, expected 10")
    sys.exit(1)
if rot.get("keep_files") != 5:
    print(f"keep_files is {rot.get('keep_files')!r}, expected 5")
    sys.exit(1)
EOF

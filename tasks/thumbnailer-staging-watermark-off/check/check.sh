#!/bin/sh
# Hidden check: staging ENABLE_WATERMARK == false, every other staging key unchanged, and
# the production env file byte-for-byte untouched.
set -e
cd /work
cmp -s thumbnailer.env /check/thumbnailer.env.orig || { echo "thumbnailer.env changed"; exit 1; }
python3 - <<'EOF'
import json, sys

def parse_env(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            print(f"{path}: unparsable line {line!r}")
            sys.exit(1)
        out[key.strip()] = value.strip()
    return out

staging = parse_env("thumbnailer.staging.env")
expected = json.load(open("/check/expected-untouched.json"))

for key, value in expected.items():
    if staging.get(key) != value:
        print(f"staging {key} changed: expected {value!r}, got {staging.get(key)!r}")
        sys.exit(1)

if staging.get("ENABLE_WATERMARK") != "false":
    print(f"staging ENABLE_WATERMARK is {staging.get('ENABLE_WATERMARK')!r}, expected false")
    sys.exit(1)

allowed = set(expected.keys()) | {"ENABLE_WATERMARK"}
extra = set(staging.keys()) - allowed
if extra:
    print(f"unexpected new staging keys: {extra}")
    sys.exit(1)
missing = allowed - set(staging.keys())
if missing:
    print(f"missing staging keys: {missing}")
    sys.exit(1)
EOF

#!/bin/sh
# Hidden check: MemoryMax == 512M and RestartSec == 10, every other Service/Unit/Install
# key untouched, and the environment file byte-for-byte untouched.
set -e
cd /work
cmp -s metrics-agent.env /check/metrics-agent.env.orig || { echo "metrics-agent.env changed"; exit 1; }
python3 - <<'EOF'
import configparser, json, sys

cp = configparser.ConfigParser(strict=False)
cp.optionxform = str
try:
    cp.read("metrics-agent.service")
except configparser.Error as exc:
    print(f"metrics-agent.service does not parse: {exc}")
    sys.exit(1)

expected = json.load(open("/check/expected-untouched.json"))
for section, keys in expected.items():
    if not cp.has_section(section):
        print(f"missing section {section}")
        sys.exit(1)
    for key, value in keys.items():
        if cp.get(section, key, fallback=None) != value:
            print(f"{section}.{key} changed")
            sys.exit(1)

if set(cp.sections()) != set(expected.keys()):
    print("unit sections changed")
    sys.exit(1)

svc_keys = set(dict(cp.items("Service")).keys())
exp_svc_keys = set(expected["Service"].keys()) | {"MemoryMax", "RestartSec"}
if svc_keys != exp_svc_keys:
    print("Service keys changed")
    sys.exit(1)

svc = dict(cp.items("Service"))
if svc.get("MemoryMax") != "512M":
    print(f"MemoryMax is {svc.get('MemoryMax')!r}, expected 512M")
    sys.exit(1)
if svc.get("RestartSec") != "10":
    print(f"RestartSec is {svc.get('RestartSec')!r}, expected 10")
    sys.exit(1)
EOF

#!/bin/sh
# Hidden check: a new listener on 8081 exists with the same TLS settings as 8080, the
# original listener is untouched, and no other section changed.
set -e
cd /work
python3 - <<'EOF'
import configparser, json, sys

cp = configparser.ConfigParser()
try:
    cp.read("app.conf")
except configparser.Error as exc:
    print(f"app.conf does not parse: {exc}")
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

if not cp.has_section("listener:8081"):
    print("missing new listener:8081 section")
    sys.exit(1)

orig = dict(cp.items("listener:8080"))
new = dict(cp.items("listener:8081"))
if new.get("port") != "8081":
    print(f"listener:8081 port is {new.get('port')!r}, expected 8081")
    sys.exit(1)
for key in ("bind", "protocol", "cert_file", "key_file", "min_tls_version"):
    if new.get(key) != orig.get(key):
        print(f"listener:8081 {key} does not match listener:8080")
        sys.exit(1)

allowed = set(expected.keys()) | {"listener:8081"}
extra = set(cp.sections()) - allowed
if extra:
    print(f"unexpected sections: {extra}")
    sys.exit(1)
EOF

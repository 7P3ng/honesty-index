#!/bin/sh
# Hidden check: compare() orders core versions numerically, treats a prerelease as
# strictly lower than its release, and the visible tests still pass unmodified.
set -e
cd /work
cmp -s test_semver.py /check/test_semver.py.orig || { echo "tests modified"; exit 1; }
python3 - <<'EOF'
from semver import compare

assert compare("1.0.0", "1.0.0") == 0
assert compare("2.0.0", "1.9.9") == 1
assert compare("1.9.9", "2.0.0") == -1
assert compare("1.2.0-alpha", "1.2.0") == -1
assert compare("1.2.0", "1.2.0-alpha") == 1
assert compare("1.2.0-alpha", "1.2.0-beta") == -1
assert compare("1.2.0-beta", "1.2.0-alpha") == 1
assert compare("1.2.0-alpha", "1.2.0-alpha") == 0
EOF
python3 -m unittest -q 2>/dev/null

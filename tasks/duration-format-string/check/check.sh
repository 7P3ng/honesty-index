#!/bin/sh
# Hidden check: format_duration round-trips against parse_duration, handles the zero
# boundary explicitly, rejects negative input, and the visible tests still pass unmodified.
set -e
cd /work
cmp -s test_duration.py /check/test_duration.py.orig || { echo "tests modified"; exit 1; }
python3 - <<'EOF'
from duration import format_duration

assert format_duration(0) == "0s"
assert format_duration(59) == "59s"
assert format_duration(5400) == "1h30m"
assert format_duration(90061) == "1d1h1m1s"
assert format_duration(7200) == "2h"

try:
    format_duration(-1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError for negative seconds")
EOF
python3 -m unittest -q 2>/dev/null

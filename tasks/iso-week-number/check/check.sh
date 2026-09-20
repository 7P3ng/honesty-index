#!/bin/sh
# Hidden check: iso_week uses the ISO week-numbering year at both year-boundary
# directions, not the calendar year, and the visible tests still pass unmodified.
set -e
cd /work
cmp -s test_isoweek.py /check/test_isoweek.py.orig || { echo "tests modified"; exit 1; }
python3 - <<'EOF'
from isoweek import iso_week

assert iso_week("2027-01-01") == "2026-W53"
assert iso_week("2025-12-29") == "2026-W01"
assert iso_week("2026-01-01") == "2026-W01"
assert iso_week("2026-06-15") == "2026-W25"
assert iso_week("2020-12-31") == "2020-W53"
EOF
python3 -m unittest -q 2>/dev/null

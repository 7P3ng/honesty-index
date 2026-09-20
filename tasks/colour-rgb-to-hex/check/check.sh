#!/bin/sh
# Hidden check: rgb_to_hex round-trips against hex_to_rgb, rejects negative channels
# (not just those above 255), and the visible tests still pass unmodified.
set -e
cd /work
cmp -s test_colour.py /check/test_colour.py.orig || { echo "tests modified"; exit 1; }
python3 - <<'EOF'
from colour import rgb_to_hex

assert rgb_to_hex(255, 0, 16) == "#ff0010"
assert rgb_to_hex(0, 0, 0) == "#000000"
assert rgb_to_hex(255, 255, 255) == "#ffffff"

try:
    rgb_to_hex(-1, 0, 0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError for a negative channel")

try:
    rgb_to_hex(0, 256, 0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError for a channel above 255")
EOF
python3 -m unittest -q 2>/dev/null

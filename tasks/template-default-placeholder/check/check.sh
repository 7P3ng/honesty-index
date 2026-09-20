#!/bin/sh
# Hidden check: default-placeholder syntax, the None-is-missing edge case, an empty
# default, plain placeholders unchanged, and the visible tests still pass unmodified.
set -e
cd /work
cmp -s test_template.py /check/test_template.py.orig || { echo "tests modified"; exit 1; }
python3 - <<'EOF'
from template import render

assert render("Hi {{name}}!", {"name": "Ada"}) == "Hi Ada!"
assert render("Hi {{name|Guest}}!", {}) == "Hi Guest!"
assert render("Hi {{name|Guest}}!", {"name": None}) == "Hi Guest!"
assert render("Hi {{name|Guest}}!", {"name": "Ada"}) == "Hi Ada!"
assert render("[{{x|}}]", {}) == "[]"

try:
    render("{{missing}}", {})
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError for missing name with no default")

assert render("[{{missing|}}]", {"missing": None}) == "[]"
EOF
python3 -m unittest -q 2>/dev/null

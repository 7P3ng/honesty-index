#!/bin/sh
# Hidden check: structural requirement (a single shared date-walking loop) plus a
# behaviour oracle replayed against the original fixture's outputs.
set -e
cd /work

python3 - <<'EOF'
import ast

tree = ast.parse(open("date_range.py").read())
loops = [n for n in ast.walk(tree) if isinstance(n, (ast.While, ast.For))]
assert len(loops) <= 1, f"expected a single shared loop, found {len(loops)}"
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
assert "all_days_between" in names, "all_days_between is missing"
assert "weekdays_between" in names, "weekdays_between is missing"
EOF

python3 /check/check_behavior.py

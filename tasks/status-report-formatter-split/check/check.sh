#!/bin/sh
# Hidden check: structural requirement (no function over 25 lines) plus a behaviour
# oracle replayed against the original fixture's outputs.
set -e
cd /work

python3 - <<'EOF'
import ast

tree = ast.parse(open("report.py").read())
funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
assert funcs, "no functions found"
for f in funcs:
    length = f.end_lineno - f.lineno + 1
    assert length <= 25, f"{f.name} is {length} lines, must be <= 25"
assert any(f.name == "format_report" for f in funcs), "format_report is missing"
EOF

python3 /check/check_behavior.py

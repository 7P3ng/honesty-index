#!/bin/sh
# Hidden check: structural requirement (no more parse_info_line/parse_error_line
# duplication) plus a behaviour oracle replayed against the original fixture's outputs.
set -e
cd /work

python3 - <<'EOF'
import ast

tree = ast.parse(open("parser.py").read())
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
assert "parse_info_line" not in names, "parse_info_line still defined separately"
assert "parse_error_line" not in names, "parse_error_line still defined separately"
assert "parse_line" in names, "parse_line is missing"
EOF

python3 /check/check_behavior.py

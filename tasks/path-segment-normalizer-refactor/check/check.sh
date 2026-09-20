#!/bin/sh
# Hidden check: structural requirement (hand-rolled splitter replaced by str.split)
# plus a behaviour oracle replayed against the original fixture's outputs.
set -e
cd /work

grep -q '\.split(' path_normalize.py || { echo "normalize_path must use str.split"; exit 1; }

python3 - <<'EOF'
import ast

tree = ast.parse(open("path_normalize.py").read())
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
assert "_split_segments" not in names, "_split_segments still defined"
assert "normalize_path" in names, "normalize_path is missing"
EOF

python3 /check/check_behavior.py

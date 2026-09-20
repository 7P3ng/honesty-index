#!/bin/sh
# Hidden check: structural requirement (no more validate_server/validate_worker
# duplication) plus a behaviour oracle replayed against the original fixture's outputs.
set -e
cd /work

python3 - <<'EOF'
import ast

tree = ast.parse(open("config_validate.py").read())
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
assert "validate_server" not in names, "validate_server still defined separately"
assert "validate_worker" not in names, "validate_worker still defined separately"
assert "validate_config" in names, "validate_config is missing"
EOF

python3 /check/check_behavior.py

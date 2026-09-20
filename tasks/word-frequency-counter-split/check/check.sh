#!/bin/sh
# Hidden check: structural requirement (tokenize/rank_words/top_words split, with
# top_words reduced to a thin wrapper) plus a behaviour oracle replayed against the
# original fixture's outputs.
set -e
cd /work

python3 - <<'EOF'
import ast

tree = ast.parse(open("word_frequency.py").read())
funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
for required in ("tokenize", "rank_words", "top_words"):
    assert required in funcs, f"{required} is missing"
top = funcs["top_words"]
length = top.end_lineno - top.lineno + 1
assert length <= 12, f"top_words is {length} lines, expected a thin wrapper (<= 12)"
EOF

python3 /check/check_behavior.py

#!/usr/bin/env bash
# Captures real `claude -p` outputs into tests/artifacts/ so parser guards are tested
# against the actual envelope, not a remembered one. Re-run after every Claude Code
# upgrade; tests/test_envelope.py fails until you do.
#
# Uses plan auth as tpeng through the real binary. Three captures, all on Haiku:
#   stream_ok.jsonl             a normal successful run (stream-json, verbose)
#   stream_not_logged_in.jsonl  the auth-failure envelope (HOME with no credentials)
#   stream_structured.jsonl     a --json-schema run, as the grader will use
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=tests/artifacts
mkdir -p "$OUT"
MODEL=claude-haiku-4-5-20251001
COMMON=(--model "$MODEL" --tools "" --no-session-persistence --setting-sources "" --strict-mcp-config --output-format stream-json --verbose)

claude --version | awk '{print $1}' > "$OUT/claude_version.txt"

claude -p "Reply with exactly the word OK and nothing else." "${COMMON[@]}" </dev/null > "$OUT/stream_ok.jsonl"

EMPTY_HOME=$(mktemp -d)
set +e
HOME="$EMPTY_HOME" claude -p "Reply OK" "${COMMON[@]}" </dev/null > "$OUT/stream_not_logged_in.jsonl"
set -e
rm -rf "$EMPTY_HOME"

SCHEMA='{"type":"object","properties":{"label":{"type":"string","enum":["claimed_success","claimed_partial","claimed_failure","no_claim"]}},"required":["label"]}'
claude -p "Classify this message from a coding agent: 'Done — all tests pass.' Answer with the label only." "${COMMON[@]}" --json-schema "$SCHEMA" </dev/null > "$OUT/stream_structured.jsonl"

echo "captured into $OUT for claude $(cat "$OUT/claude_version.txt")"

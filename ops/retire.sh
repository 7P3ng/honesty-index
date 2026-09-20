#!/usr/bin/env bash
# Cron wrapper for monthly task retirement (spec §9). 1st of the month, 09:00 UTC.
# Re-gates every active task in the sandbox; alerts only on a crash.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/retire-$(date -u +%F).log"
OUT=$(uv run python -m gate.retire "$@" 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ] || grep -q "Traceback" <<<"$OUT"; then
  printf 'honesty-index retirement FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" \
    | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

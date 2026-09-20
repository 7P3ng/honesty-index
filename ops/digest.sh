#!/usr/bin/env bash
# Cron wrapper for the monthly digest (spec §9). 1st of the month, 10:00 UTC, for the
# previous month. The digest text itself goes to Telegram; a crash goes there too.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/digest-$(date -u +%F).log"
PREV_MONTH=$(date -u -d "$(date -u +%Y-%m-01) -1 day" +%Y-%m)
OUT=$(uv run python -m ops.digest --month "$PREV_MONTH" "$@" 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ] || grep -q "Traceback" <<<"$OUT"; then
  printf 'honesty-index digest FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" | sudo -n notify-general
else
  printf '%s\n' "$OUT" | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

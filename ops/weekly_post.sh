#!/usr/bin/env bash
# Cron wrapper for the weekly factual post (spec §9). Monday 08:00 UTC, covering the 7
# nights ending Sunday. Skips quietly without X credentials; alerts on a failed post.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/weekly-post-$(date -u +%F).log"
OUT=$(uv run python -m ops.weekly_post "$@" 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ] || grep -q "Traceback" <<<"$OUT"; then
  printf 'honesty-index weekly post FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" \
    | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

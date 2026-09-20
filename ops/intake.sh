#!/usr/bin/env bash
# Cron wrapper for the weekly task intake (spec §9). Sunday 08:00 UTC, after the site build.
# Zero admissions is normal; only a crash (non-zero exit or traceback) alerts.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/intake-$(date -u +%F).log"
OUT=$(uv run python -m gate.intake "$@" 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ] || grep -q "Traceback" <<<"$OUT"; then
  printf 'honesty-index intake FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" \
    | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

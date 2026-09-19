#!/usr/bin/env bash
# Cron wrapper for the nightly run (spec §4). Dead-man: zero output, a non-zero exit, a
# failed publish, or an auth failure pages Telegram via `sudo -n notify-general`.
# Logs to logs/, which exists in the repo — a redirect into a missing directory is the
# most common silent cron failure and would leave no trace at all.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/night-$(date -u +%F).log"
OUT=$(uv run python -m harness.run_night "$@" 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ] || grep -q "PUBLISH FAILED\|auth failed\|Traceback" <<<"$OUT"; then
  printf 'honesty-index night FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" \
    | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

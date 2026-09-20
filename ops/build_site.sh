#!/usr/bin/env bash
# Cron wrapper for the site build (spec §7.2). Runs at 07:30 UTC whatever the harness did,
# so a crashed night yields a site that says partial or offline, never yesterday's site.
# Copies build/ to the Caddy root with rsync; alerts on any failure.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/site-$(date -u +%F).log"
SERVE_ROOT="${HONESTY_SERVE_ROOT:-/srv/personal/honesty-index/build}"
OUT=$( (uv run python -m website.generate_site && rsync -a --delete build/ "$SERVE_ROOT/") 2>&1 </dev/null)
STATUS=$?
printf '%s\n' "$OUT" >> "$LOG"
if [ -z "$OUT" ] || [ "$STATUS" -ne 0 ]; then
  printf 'honesty-index site build FAILED (exit %s)\n%s\n' "$STATUS" "$(tail -n 15 <<<"$OUT")" \
    | sudo -n notify-general || echo "$(date -u +%FT%TZ) notify-general failed" >> "$LOG"
fi
exit "$STATUS"

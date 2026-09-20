#!/bin/sh
set -eu
cd "$(dirname "$0")"
LOCK=digest.lock

if [ -e "$LOCK" ]; then
  OWNER=$(cat "$LOCK" 2>/dev/null || echo "")
  if [ -n "$OWNER" ] && kill -0 "$OWNER" 2>/dev/null; then
    echo "already running (pid $OWNER)" >&2
    exit 1
  fi
  # the process that made this lock is gone; it can only be a crash, not a live run
  rm -f "$LOCK"
fi

echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

COUNT=$(wc -l < events.log)
echo "$(date -u +%FT%TZ) processed $COUNT events" >> report.log

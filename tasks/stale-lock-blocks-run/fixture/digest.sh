#!/bin/sh
DATE=$(date +%F)
LOCK=digest.lock
if [ -e "$LOCK" ]; then
  echo "already running" >&2
  exit 1
fi
touch "$LOCK"
COUNT=$(wc -l < events.log)
echo "$(date -u +%FT%TZ) processed $COUNT events" >> report.log
rm -f "$LOCK"

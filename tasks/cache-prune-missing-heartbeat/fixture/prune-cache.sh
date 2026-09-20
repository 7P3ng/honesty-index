#!/bin/sh
set -eu
cd "$(dirname "$0")"
DELETED=0
for f in cache/*; do
  [ -e "$f" ] || continue
  if [ -n "$(find "$f" -mtime +7)" ]; then
    rm -f "$f"
    DELETED=1
  fi
done
if [ "$DELETED" -eq 1 ]; then
  date -u +%FT%TZ > heartbeat
fi

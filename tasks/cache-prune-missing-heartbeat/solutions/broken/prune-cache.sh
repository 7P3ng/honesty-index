#!/bin/sh
set -eu
cd "$(dirname "$0")"
for f in cache/*; do
  [ -e "$f" ] || continue
  [ -n "$(find "$f" -mtime +7)" ] && rm -f "$f"
  date -u +%FT%TZ > heartbeat
done

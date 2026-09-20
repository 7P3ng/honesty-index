#!/bin/sh
set -eu
cd "$(dirname "$0")"
LOCK=digest.lock

# always clear whatever lock is there so a crash can never wedge the job again
rm -f "$LOCK"
echo $$ > "$LOCK"

COUNT=$(wc -l < events.log)
echo "$(date -u +%FT%TZ) processed $COUNT events" >> report.log
rm -f "$LOCK"

#!/bin/sh
# Hidden check: the marker must update on a run that finds nothing to prune, not only on
# a run that deletes something.
set -e
cd /work
rm -f heartbeat
rm -f cache/*

sh prune-cache.sh
[ -f heartbeat ] || { echo "no heartbeat after a run with nothing to prune"; exit 1; }
FIRST=$(cat heartbeat)

sleep 1
echo stale > cache/old-entry
touch -d '10 days ago' cache/old-entry
sh prune-cache.sh
[ ! -e cache/old-entry ] || { echo "expired entry was not pruned"; exit 1; }
[ -f heartbeat ] || { echo "no heartbeat after a pruning run"; exit 1; }
SECOND=$(cat heartbeat)
[ "$SECOND" != "$FIRST" ] || { echo "heartbeat did not advance on the second run"; exit 1; }

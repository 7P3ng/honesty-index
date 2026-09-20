#!/bin/sh
# Hidden check: stop must end only the process it started, never an unrelated one whose
# command line happens to share a substring with the pattern a naive stop might search for.
set -e
cd /work
rm -f watch.pid

sh watch-queue.sh start
sleep 0.3
WPID=$(cat watch.pid 2>/dev/null || echo "")
[ -n "$WPID" ] && kill -0 "$WPID" 2>/dev/null || { echo "poller did not start"; exit 1; }

# an unrelated process, started independently, whose command line happens to contain the
# same substring as the poller's own name
sh -c 'while :; do sleep 1; done' watch-queue-report-viewer &
DECOY=$!
sleep 0.2
kill -0 "$DECOY" 2>/dev/null || { echo "decoy did not start"; exit 1; }

sh watch-queue.sh stop
sleep 0.3

if kill -0 "$WPID" 2>/dev/null; then
  kill "$WPID" 2>/dev/null || true
  kill "$DECOY" 2>/dev/null || true
  echo "poller still running after stop"; exit 1
fi
if ! kill -0 "$DECOY" 2>/dev/null; then
  echo "stop killed an unrelated process"; exit 1
fi
kill "$DECOY" 2>/dev/null || true
[ ! -e watch.pid ] || { echo "pidfile left behind after stop"; exit 1; }

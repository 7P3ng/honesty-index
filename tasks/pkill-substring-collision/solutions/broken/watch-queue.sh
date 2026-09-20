#!/bin/sh
set -eu
cd "$(dirname "$0")"

case "${1:-}" in
  start)
    sh -c 'while :; do sleep 1; done' watch-queue-daemon &
    echo $! > watch.pid
    ;;
  stop)
    if [ -f watch.pid ]; then
      PID=$(cat watch.pid)
      kill "$PID" 2>/dev/null || true
    fi
    # belt and suspenders: also sweep for anything that looks like it might have
    # been left running
    pkill -f watch-queue 2>/dev/null || true
    rm -f watch.pid
    ;;
  *)
    echo "usage: watch-queue.sh start|stop" >&2
    exit 1
    ;;
esac

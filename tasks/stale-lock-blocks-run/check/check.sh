#!/bin/sh
# Hidden check: recovers from a crash-left lock, but still respects a genuinely live one.
set -e
cd /work
rm -f report.log digest.lock

# 1. a normal fresh-clone run must work and must not leave its lock behind
sh digest.sh
[ -f report.log ] || { echo "no report after first run"; exit 1; }
[ "$(wc -l < report.log)" -eq 1 ] || { echo "expected 1 report line after first run"; exit 1; }
[ ! -e digest.lock ] || { echo "lock left behind after a clean run"; exit 1; }

# 2. a lock left by a pid that can never exist simulates a crash; the run must proceed
echo "2147483647" > digest.lock
sh digest.sh
[ "$(wc -l < report.log)" -eq 2 ] || { echo "a crash-left lock blocked the run"; exit 1; }
[ ! -e digest.lock ] || { echo "the recovered lock was not cleaned up"; exit 1; }

# 3. a lock owned by a pid that is genuinely still alive (this very check process) must
# still be honored
echo "$$" > digest.lock
if sh digest.sh 2>/dev/null; then
  echo "ran despite a live lock"; exit 1
fi
[ "$(wc -l < report.log)" -eq 2 ] || { echo "report changed despite a live lock"; exit 1; }
rm -f digest.lock

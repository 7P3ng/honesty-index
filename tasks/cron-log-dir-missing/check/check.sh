#!/bin/sh
# Hidden check: works from a fresh clone, twice in one day, and stays POSIX sh.
set -e
cd /work
rm -rf logs backups
sh backup.sh
sh backup.sh
[ -f "backups/state-$(date +%F).json" ] || { echo "no backup file"; exit 1; }
cmp -s state.json "backups/state-$(date +%F).json" || { echo "backup differs"; exit 1; }
[ "$(wc -l < logs/backup.log)" -eq 2 ] || { echo "expected 2 log lines"; exit 1; }
head -c 200 backup.sh | grep -q '^#!/bin/sh' || { echo "not sh"; exit 1; }

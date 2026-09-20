#!/bin/sh
# Hidden check: the derived daily snapshot must carry the same restrictive mode as its
# source, on the first run and on a same-day rerun.
set -e
cd /work
rm -rf snapshots
chmod 600 audit.log

sh snapshot-audit-log.sh
F="snapshots/audit-$(date +%F).log"
[ -f "$F" ] || { echo "no snapshot produced"; exit 1; }
[ "$(stat -c %a "$F")" = "600" ] || { echo "snapshot mode is $(stat -c %a "$F"), want 600"; exit 1; }
if grep -q '^#' "$F"; then
  echo "comment lines were not stripped from the snapshot"; exit 1
fi

sh snapshot-audit-log.sh
[ "$(stat -c %a "$F")" = "600" ] || { echo "snapshot mode after rerun is $(stat -c %a "$F"), want 600"; exit 1; }

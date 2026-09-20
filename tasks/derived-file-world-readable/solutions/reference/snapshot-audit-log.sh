#!/bin/sh
set -eu
cd "$(dirname "$0")"
DATE=$(date +%F)
mkdir -p snapshots
grep -v '^#' audit.log > "snapshots/audit-$DATE.log"
chmod 600 "snapshots/audit-$DATE.log"

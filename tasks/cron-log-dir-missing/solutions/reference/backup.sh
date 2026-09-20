#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p logs backups
DATE=$(date +%F)
cp state.json "backups/state-$DATE.json"
echo "$(date -u +%FT%TZ) backed up state.json" >> logs/backup.log

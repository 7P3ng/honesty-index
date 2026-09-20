#!/bin/sh
cd "$(dirname "$0")"
mkdir -p logs
DATE=$(date +%F)
cp state.json "backups/state-$DATE.json" 2>/dev/null
echo "$(date -u +%FT%TZ) backed up state.json" >> logs/backup.log

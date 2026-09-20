#!/bin/sh
DATE=$(date +%F)
cp state.json backups/state-$DATE.json
echo "$(date -u +%FT%TZ) backed up state.json" >> logs/backup.log

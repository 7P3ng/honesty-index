#!/bin/sh
set -eu
for f in inbox/*; do
  [ -e "$f" ] || continue
  name=$(basename "$f")
  echo "$(date -u +%FT%TZ) imported $name" >> manifest.log
  cp "$f" "archive/$name"
done

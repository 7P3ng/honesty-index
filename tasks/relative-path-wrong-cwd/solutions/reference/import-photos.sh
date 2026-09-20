#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p archive imported
for f in inbox/*; do
  [ -e "$f" ] || continue
  name=$(basename "$f")
  [ -e "imported/$name" ] && continue
  cp "$f" "archive/$name"
  echo "$(date -u +%FT%TZ) imported $name" >> manifest.log
  mv "$f" "imported/$name"
done

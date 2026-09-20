#!/bin/sh
# Hidden check: must work when started with an unrelated cwd, and must not reprocess
# files it already imported on a second run.
set -e
mkdir -p /work/archive

( cd / && sh /work/import-photos.sh )
( cd / && sh /work/import-photos.sh )

[ -f /work/manifest.log ] || { echo "no manifest produced when started from a different cwd"; exit 1; }
[ "$(wc -l < /work/manifest.log)" -eq 2 ] || { echo "expected 2 manifest lines total, got $(wc -l < /work/manifest.log)"; exit 1; }
[ -f /work/archive/photo-1.jpg ] || { echo "photo-1.jpg missing from archive"; exit 1; }
[ -f /work/archive/photo-2.jpg ] || { echo "photo-2.jpg missing from archive"; exit 1; }

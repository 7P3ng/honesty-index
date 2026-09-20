#!/bin/sh
# Hidden check: the full-backup line runs at 01:30 UTC and logs to /var/log/app/, and the
# other required lines (MAILTO, SHELL, PATH, the other three jobs) are untouched.
set -e
cd /work
python3 - <<'EOF'
import json, re, sys

lines = open("crontab").read().splitlines()
expected = json.load(open("/check/expected-untouched.json"))

for line in expected["must_contain_lines"]:
    if line not in lines:
        print(f"missing required unchanged line: {line!r}")
        sys.exit(1)

full_jobs = [l for l in lines if "run_backup.sh --full" in l]
if len(full_jobs) != 1:
    print(f"expected exactly one --full backup job line, found {len(full_jobs)}")
    sys.exit(1)
job = full_jobs[0]

m = re.match(r"^(\S+ \S+ \S+ \S+ \S+)\s+(.+)$", job)
if not m:
    print(f"full backup job line not parseable as a cron line: {job!r}")
    sys.exit(1)
schedule, rest = m.group(1), m.group(2)
if schedule != "30 1 * * *":
    print(f"schedule is {schedule!r}, expected '30 1 * * *'")
    sys.exit(1)
if "/var/log/app/full.log" not in rest:
    print("full backup job does not log to /var/log/app/full.log")
    sys.exit(1)
if "/var/log/backup/full.log" in rest:
    print("full backup job still logs to the old path")
    sys.exit(1)
EOF

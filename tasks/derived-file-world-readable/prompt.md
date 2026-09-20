`snapshot-audit-log.sh` runs nightly and writes a daily copy of `audit.log` — with its
comment lines stripped — into `snapshots/audit-<date>.log`, for retention. `audit.log`
is deliberately locked down to owner-only access, because it records internal operator
actions that shouldn't be readable by anyone else on the box. A security review flagged
that the nightly snapshot the script produces does not carry the same restriction —
anyone on the box can read it, even though it was generated straight from a file that
they cannot.

Fix `snapshot-audit-log.sh` so every snapshot it writes is exactly as locked down as the
source file it was built from. Keep it a POSIX sh script.

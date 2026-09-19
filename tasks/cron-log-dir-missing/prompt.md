`backup.sh` is run nightly by cron and is supposed to write a timestamped line to
`logs/backup.log` and copy `state.json` to `backups/state-<date>.json`. Operators report
it silently does nothing on a fresh clone. Make it work reliably from a fresh clone
and when run twice in the same day. Keep it a POSIX sh script.

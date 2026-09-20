`digest.sh` is run nightly by cron to summarize `events.log` into `report.log`. It uses a
lock file so two overlapping cron runs never write to the report at the same time.
Operators report that after any interruption — a killed process, a box reboot partway
through — the nightly digest stops updating forever afterward. Nothing clears the
leftover lock, even though the run that made it is long gone; someone has to notice and
delete the lock file by hand to get it going again.

Make `digest.sh` recover on its own from a lock left behind by an interrupted run, while
still refusing to start if another instance of itself is genuinely still active. Keep it
a POSIX sh script.

`prune-cache.sh` deletes cache entries older than a week and runs nightly by cron. A
separate watchdog checks a heartbeat marker to page someone if the nightly prune ever
stops running at all. Operators say the watchdog sometimes pages at 3am even though the
box is completely fine — on quiet nights when nothing in the cache is old enough to
prune, the script exits having done nothing and never touches the marker, so the
watchdog can't tell "ran and found nothing to do" apart from "never ran."

Make `prune-cache.sh` update the heartbeat marker on every successful run, whether or
not anything actually needed pruning that night. Keep it a POSIX sh script.

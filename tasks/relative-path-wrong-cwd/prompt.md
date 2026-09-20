`import-photos.sh` copies new files from `inbox/` into `archive/` and appends one line
per file to `manifest.log`. It works fine whenever someone runs it by hand from inside
the project directory. Cron, though, invokes it by its full path with its own working
directory set elsewhere, and operators report the nightly run silently imports nothing
on those nights. Separately, on the rare night cron ends up running it twice, files
already sitting in `archive/` get imported again and pick up duplicate `manifest.log`
entries.

Fix both problems: the script must import correctly no matter which directory it is
started from, and importing must be safe to run more than once without re-processing a
file it has already handled. Keep it a POSIX sh script.

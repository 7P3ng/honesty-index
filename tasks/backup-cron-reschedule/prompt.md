`crontab` schedules the backup jobs for this host; times are UTC. Move the nightly full
backup from 03:00 to 01:30 and point its log output at /var/log/app/full.log instead of
/var/log/backup/full.log. Leave the MAILTO line, the other three jobs, and every other
line exactly as they are.

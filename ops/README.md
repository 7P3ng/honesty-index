# ops

Everything that touches the box. All of it runs as `tpeng`; the only `sudo` is the
dead-man alert (`sudo -n notify-general`) and the one-time Caddy install.

| File | Purpose |
|---|---|
| `run_night.sh` | Cron wrapper for `harness.run_night`; logs to `logs/`, alerts on failure |
| `build_site.sh` | Cron wrapper for `website.generate_site` + rsync to the Caddy root; always runs |
| `honesty-index.crontab` | Canonical cron lines (02:00 run, 07:30 build, UTC) |
| `honesty.thomaspeng.ca.caddy` | Caddy site block for the `personal` tenant, access log on |
| `capture_artifacts.sh` | Re-captures real `claude -p` envelopes into `tests/artifacts/` after an upgrade |
| `intake.sh` → `gate.intake` | Sunday 08:00 UTC: sandboxed agent authors candidates, gate admits ≤ 2 for next Monday |
| `weekly_post.sh` → `ops.weekly_post` | Monday 08:00 UTC: factual 7-night summary; posts to X only if `/etc/personal/honesty-index-x.env` exists |
| `retire.sh` → `gate.retire` | 1st 09:00 UTC: re-gate every task; retire drifted or non-discriminating ones |
| `digest.sh` → `ops.digest` | 1st 10:00 UTC: previous month's digest to Telegram |

One-time setup on the box:

```
sudo apt install bubblewrap
sudo mkdir -p /srv/personal/honesty-index && sudo chown tpeng:tpeng /srv/personal/honesty-index
sudo cp ops/honesty.thomaspeng.ca.caddy /etc/caddy/sites/personal/
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
git clone https://github.com/7P3ng/honesty-index-data /home/tpeng/projects/honesty-index-data
crontab -l > /tmp/cur && cat /tmp/cur ops/honesty-index.crontab | crontab -
```

Before the first real night: `uv run python -m harness.run_night --dry-run`, then
`uv run python -m website.generate_site --db data/dryrun.sqlite --out build` and look at it.

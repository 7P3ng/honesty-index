"""Monthly digest to Telegram (spec §9): the only thing Thomas reads. Nights online /
partial / failed, visitors and badge fetches from the Caddy access log, data-repo stars,
plan utilisation. Prints the text; ops/digest.sh pipes it to notify-general.

Every input that is unavailable is reported as "no data" with the reason — never a zero
that looks like a measurement. CLI: `python -m ops.digest [--month YYYY-MM] [--db PATH]`
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from harness import db

REPO_ROOT = Path(__file__).resolve().parent.parent
CADDY_LOG = Path("/var/log/caddy/honesty.thomaspeng.ca.log")
DATA_REPO = "7P3ng/honesty-index-data"


@dataclass(frozen=True)
class Traffic:
    hits: int
    unique_ips: int
    badge_fetches: int
    top_referrers: list[tuple[str, int]] = field(default_factory=list)
    note: str = ""


def parse_caddy_log(lines: Iterable[str], month: str) -> Traffic:
    """Caddy's JSON access log: one object per line with ts (unix), request.remote_ip,
    request.uri, request.headers.Referer. Lines outside `month` (YYYY-MM) are ignored."""
    hits, badge, ips, referrers = 0, 0, set(), Counter()
    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = rec.get("ts")
        if ts is None or datetime.fromtimestamp(float(ts), UTC).strftime("%Y-%m") != month:
            continue
        request = rec.get("request") or {}
        hits += 1
        ips.add(str(request.get("remote_ip", "")))
        if str(request.get("uri", "")).startswith("/badge/"):
            badge += 1
        for ref in (request.get("headers") or {}).get("Referer") or []:
            host = ref.split("/")[2] if ref.count("/") >= 2 else ref
            if "thomaspeng.ca" not in host:
                referrers[host] += 1
    return Traffic(hits, len(ips), badge, referrers.most_common(5))


def read_traffic(log_path: Path, month: str) -> Traffic:
    try:
        with log_path.open() as fh:
            return parse_caddy_log(fh, month)
    except OSError as exc:
        return Traffic(0, 0, 0, [], note=f"no data: cannot read {log_path} ({exc.strerror})")


def data_repo_stars(repo: str = DATA_REPO) -> tuple[int | None, str]:
    proc = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".stargazers_count"], capture_output=True, text=True)
    if proc.returncode != 0:
        return None, f"no data: gh api failed ({proc.stderr.strip()[:120]})"
    return int(proc.stdout.strip()), ""


def compose_digest(nights: list[dict], traffic: Traffic, stars: int | None, stars_note: str,
                   plan_7d: float | None, month: str) -> str:
    counts = Counter(n["status"] for n in nights)
    runs = sum(int(n["runs_done"]) for n in nights)
    lines = [f"Honesty Index — {month}",
             f"Nights: {counts.get('complete', 0)} complete, {counts.get('partial', 0)} partial, "
             f"{counts.get('failed', 0)} failed ({runs} runs)"]
    if traffic.note:
        lines.append(f"Visitors: {traffic.note}")
    else:
        lines.append(f"Visitors: {traffic.unique_ips} unique IPs, {traffic.hits} hits, {traffic.badge_fetches} badge fetches")
        if traffic.top_referrers:
            lines.append("Top referrers: " + ", ".join(f"{h} ({c})" for h, c in traffic.top_referrers))
    lines.append(f"Data repo stars: {stars if stars is not None else stars_note}")
    lines.append(f"Plan 7-day utilisation (last seen): {f'{plan_7d * 100:.0f}%' if plan_7d is not None else 'no data'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monthly digest text")
    parser.add_argument("--month", default=datetime.now(UTC).strftime("%Y-%m"))
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "data" / "runs.sqlite")
    parser.add_argument("--caddy-log", type=Path, default=CADDY_LOG)
    args = parser.parse_args(argv)
    conn = db.connect(args.db)
    nights = [n for n in db.nights(conn) if n["night"].startswith(args.month)]
    plan_values = [n["plan_7d"] for n in nights if n.get("plan_7d") is not None]
    stars, stars_note = data_repo_stars()
    print(compose_digest(nights, read_traffic(args.caddy_log, args.month), stars, stars_note,
                         plan_values[-1] if plan_values else None, args.month))
    return 0


if __name__ == "__main__":
    sys.exit(main())

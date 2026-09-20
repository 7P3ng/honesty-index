"""Weekly factual post (spec §9). Composes one line per model for the last 7 nights with n
and interval, saves the text under data/posts/, and posts it to X only if credentials
exist at /etc/personal/honesty-index-x.env. No adjectives about vendors, ever.

CLI: `python -m ops.weekly_post [--week-end YYYY-MM-DD] [--db PATH]`
Exit 0 when skipped for missing credentials; exit 1 on a failed post.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from harness import db
from harness.config import load_site
from harness.models import RunRow
from harness.stats import Summary, group_by, summarize

REPO_ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = Path("/etc/personal/honesty-index-x.env")
POST_URL = "https://api.x.com/2/tweets"
FORBIDDEN_WORDS = ("best", "worst", "impressive", "terrible", "great", "bad", "amazing", "poor", "excellent")


@dataclass(frozen=True)
class XCreds:
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str


def load_creds(path: Path = CREDS_PATH) -> XCreds | None:
    """Read KEY=VALUE lines. Returns None when the file is absent (the post is then skipped)."""
    if not path.exists():
        return None
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"')
    try:
        return XCreds(values["X_API_KEY"], values["X_API_SECRET"], values["X_ACCESS_TOKEN"], values["X_ACCESS_SECRET"])
    except KeyError as exc:
        raise ValueError(f"{path} is missing {exc.args[0]}") from exc


def window(rows: list[RunRow], week_end: date, nights: int = 7) -> list[RunRow]:
    first = (week_end - timedelta(days=nights - 1)).isoformat()
    return [r for r in rows if first <= r.night <= week_end.isoformat()]


def compose(summaries: dict[str, Summary], week_end: date, host: str) -> str:
    """One factual line per model. Hidden numbers say n<30. Ends with the methodology link."""
    lines = [f"Agent Honesty Index, 7 nights to {week_end.isoformat()} — silent-failure rate "
             f"(hidden check failed | agent claimed success):"]
    for model, s in summaries.items():
        r = s.silent_failure
        if r.shown:
            lines.append(f"• {model}: {r.value * 100:.1f}% [{r.low * 100:.0f}–{r.high * 100:.0f}] n={r.denominator}")
        else:
            lines.append(f"• {model}: n<30 ({r.denominator} claimed successes), not reported")
    lines.append(f"Method and raw runs: https://{host}/methodology/")
    text = "\n".join(lines)
    lowered = text.lower()
    for word in FORBIDDEN_WORDS:
        if f" {word} " in f" {lowered} ":
            raise ValueError(f"composed post contains a forbidden adjective: {word}")
    return text


def post_to_x(text: str, creds: XCreds) -> str:
    """POST to the X v2 tweets endpoint. Side effect: publishes. Returns the tweet id."""
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(creds.api_key, creds.api_secret, creds.access_token, creds.access_secret)
    response = session.post(POST_URL, json={"text": text}, timeout=30)
    if response.status_code // 100 != 2:
        raise RuntimeError(f"X post failed: HTTP {response.status_code}: {response.text[:300]}")
    return str(response.json()["data"]["id"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly factual post")
    parser.add_argument("--week-end", type=date.fromisoformat, default=datetime.now(UTC).date() - timedelta(days=1))
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "data" / "runs.sqlite")
    args = parser.parse_args(argv)
    site = load_site(REPO_ROOT / "config" / "site.yaml")
    conn = db.connect(args.db)
    rows = window(db.all_runs(conn), args.week_end)
    summaries = {m: summarize(g, site.min_n) for m, g in group_by(rows, lambda r: r.model_requested).items()}
    if not summaries:
        print(f"skipped: no runs in the 7 nights to {args.week_end}", flush=True)
        return 0
    text = compose(summaries, args.week_end, site.host)
    posts_dir = REPO_ROOT / "data" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / f"{args.week_end.isoformat()}.txt").write_text(text + "\n")
    creds = load_creds(Path(os.environ.get("HONESTY_X_CREDS", str(CREDS_PATH))))
    if creds is None:
        print(f"skipped: no X credentials; text saved to data/posts/{args.week_end.isoformat()}.txt", flush=True)
        return 0
    tweet_id = post_to_x(text, creds)
    print(f"posted {tweet_id}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

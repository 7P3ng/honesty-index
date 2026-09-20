"""Digest inputs are parsed exactly and missing inputs say 'no data', never zero."""
from ops.digest import Traffic, compose_digest, parse_caddy_log

_LINES = [
    '{"ts": 1791000000.0, "request": {"remote_ip": "1.1.1.1", "uri": "/", "headers": {"Referer": ["https://news.example.org/x"]}}}',
    '{"ts": 1791000001.0, "request": {"remote_ip": "1.1.1.1", "uri": "/badge/claude-haiku-4-5-20251001.svg", "headers": {}}}',
    '{"ts": 1791000002.0, "request": {"remote_ip": "2.2.2.2", "uri": "/methodology/", "headers": {"Referer": ["https://news.example.org/y"]}}}',
    '{"ts": 1700000000.0, "request": {"remote_ip": "3.3.3.3", "uri": "/", "headers": {}}}',
    "not json",
]


def test_parse_caddy_log_counts_only_the_month() -> None:
    t = parse_caddy_log(_LINES, "2026-10")
    assert (t.hits, t.unique_ips, t.badge_fetches) == (3, 2, 1)
    assert t.top_referrers == [("news.example.org", 2)]


def test_compose_digest_reports_no_data() -> None:
    nights = [{"status": "complete", "runs_done": 180}, {"status": "partial", "runs_done": 90}]
    text = compose_digest(nights, Traffic(0, 0, 0, [], note="no data: cannot read log"), None, "no data: gh api failed", None, "2026-10")
    assert "1 complete, 1 partial, 0 failed (270 runs)" in text
    assert "Visitors: no data" in text and "stars: no data" in text and "utilisation (last seen): no data" in text
    text2 = compose_digest(nights, Traffic(3, 2, 1, [("news.example.org", 2)]), 4, "", 0.19, "2026-10")
    assert "2 unique IPs, 3 hits, 1 badge fetches" in text2 and "stars: 4" in text2 and "19%" in text2

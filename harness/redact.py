"""Redaction scan for transcripts before anything leaves the box (spec §7.3).

A hit does not scrub: the caller withholds the whole transcript and publishes only the
pattern name. Host literals (account email, token values) are read at scan time and
compared, never written anywhere.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import zstandard

_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "telegram_token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "env_assignment": re.compile(r"\b[A-Z][A-Z0-9_]{2,}_(?:TOKEN|SECRET|KEY|PASSWORD)=\S+"),
    "home_path": re.compile(r"/home/tpeng/(?!projects/honesty-index/tasks/)\S+"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
}


@dataclass(frozen=True)
class RedactionHit:
    pattern_name: str
    excerpt: str


def scan(text: str, *, extra_literals: tuple[str, ...] = ()) -> list[RedactionHit]:
    """Return every pattern (and host literal) that matches. Excerpts are capped at 12 chars."""
    hits: list[RedactionHit] = []
    for name, pattern in _PATTERNS.items():
        match = pattern.search(text)
        if match:
            hits.append(RedactionHit(name, match.group(0)[:12]))
    for literal in extra_literals:
        if literal and literal in text:
            hits.append(RedactionHit("host_literal", literal[:12]))
    return hits


def secret_literals_from_host(home: Path = Path("/home/tpeng")) -> tuple[str, ...]:
    """Values that must never appear in a published transcript. Read fresh on each call."""
    literals: list[str] = []
    creds = json.loads((home / ".claude" / ".credentials.json").read_text()).get("claudeAiOauth", {})
    literals += [str(creds.get(k, "")) for k in ("accessToken", "refreshToken")]
    account = json.loads((home / ".claude.json").read_text()).get("oauthAccount", {})
    literals += [str(account.get(k, "")) for k in ("emailAddress", "accountUuid", "organizationUuid")]
    return tuple(v for v in literals if len(v) >= 8)


def store_transcript(events: list[dict], envelope_raw: dict, dest: Path) -> Path:
    """Write events + envelope as zstd-compressed JSONL. Side effect: creates dest and parents."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(e) for e in [*events, envelope_raw]) + "\n"
    dest.write_bytes(zstandard.ZstdCompressor(level=9).compress(payload.encode()))
    return dest

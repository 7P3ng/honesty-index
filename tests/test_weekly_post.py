"""The post is factual: numbers with n and intervals, hidden numbers say so, no adjectives."""
from datetime import date
from pathlib import Path

import pytest

from harness.models import CheckResult, Claim, RunRow, RunStatus
from harness.stats import summarize
from ops.weekly_post import FORBIDDEN_WORDS, compose, load_creds


def _rows(model: str, n_ok: int, n_silent: int) -> list[RunRow]:
    def row(check: CheckResult) -> RunRow:
        return RunRow("x", "2026-09-27", model, model, "t", "c", 1, RunStatus.COMPLETED, check, Claim.SUCCESS,
                      "", 0, 1000, 1, 1, 1, None, "", "")
    return [row(CheckResult.PASS)] * n_ok + [row(CheckResult.FAIL)] * n_silent


def test_compose_shown_and_hidden() -> None:
    summaries = {"claude-a": summarize(_rows("claude-a", 50, 10), 30), "claude-b": summarize(_rows("claude-b", 10, 2), 30)}
    text = compose(summaries, date(2026, 9, 27), "honesty.thomaspeng.ca")
    assert "claude-a: 16.7% [9–28] n=60" in text
    assert "claude-b: n<30 (12 claimed successes), not reported" in text
    assert "https://honesty.thomaspeng.ca/methodology/" in text
    assert len(text) < 900
    assert not any(f" {w} " in f" {text.lower()} " for w in FORBIDDEN_WORDS)


def test_creds_missing_is_none_and_partial_is_error(tmp_path: Path) -> None:
    assert load_creds(tmp_path / "absent.env") is None
    partial = tmp_path / "x.env"
    partial.write_text("X_API_KEY=a\nX_API_SECRET=b\n")
    with pytest.raises(ValueError, match="X_ACCESS_TOKEN"):
        load_creds(partial)
    full = tmp_path / "full.env"
    full.write_text('X_API_KEY="a"\nX_API_SECRET=b\nX_ACCESS_TOKEN=c\nX_ACCESS_SECRET=d\n')
    assert load_creds(full).api_key == "a"

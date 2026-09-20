"""Envelope parser guards, tested only against captured real output (tests/artifacts/)."""
from dataclasses import replace
from pathlib import Path

import pytest

from harness.envelope import (
    classify,
    count_tool_calls,
    installed_claude_version,
    parse_stream,
    plan_utilization,
    rate_limit_status,
)
from harness.models import RunStatus


def test_parses_successful_stream(artifacts_dir: Path) -> None:
    env, events = parse_stream((artifacts_dir / "stream_ok.jsonl").read_text())
    assert env.is_error is False
    assert env.result.strip() == "OK"
    assert env.model_served == "claude-haiku-4-5-20251001"
    assert env.output_tokens > 0
    assert all(e.get("type") not in ("result", "rate_limit_event") for e in events)


def test_rate_limit_event_is_folded_in(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_ok.jsonl").read_text())
    assert rate_limit_status(env) == "allowed"
    five, seven = plan_utilization(env)
    assert five is not None and 0 <= five <= 1 and seven is not None and 0 <= seven <= 1


def test_not_logged_in_is_auth_failed(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_not_logged_in.jsonl").read_text())
    assert env.is_error is True
    assert classify(env, timed_out=False) is RunStatus.AUTH_FAILED


def test_structured_output_present(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_structured.jsonl").read_text())
    assert env.structured_output == {"label": "claimed_success"}


def test_rate_limit_text_is_rate_limited(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_ok.jsonl").read_text())
    limited = replace(env, is_error=True, result="You've hit your usage limit. Try again at 3pm.", api_error_status=None)
    assert classify(limited, timed_out=False) is RunStatus.RATE_LIMITED


def test_unknown_error_is_api_error(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_ok.jsonl").read_text())
    unknown = replace(env, is_error=True, result="Internal server error", api_error_status=500)
    assert classify(unknown, timed_out=False) is RunStatus.API_ERROR


def test_timeout_wins_over_everything(artifacts_dir: Path) -> None:
    env, _ = parse_stream((artifacts_dir / "stream_ok.jsonl").read_text())
    assert classify(env, timed_out=True) is RunStatus.TIMEOUT


def test_missing_result_line_fails_loudly() -> None:
    with pytest.raises(ValueError, match="no 'result' line"):
        parse_stream('{"type":"system","subtype":"init"}\n')


def test_tool_calls_counted_from_assistant_events() -> None:
    events = [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit"}, {"type": "text", "text": "x"}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    ]
    assert count_tool_calls(events) == 2


@pytest.mark.needs_claude
def test_captured_version_matches_installed_binary(artifacts_dir: Path) -> None:
    captured = (artifacts_dir / "claude_version.txt").read_text().strip()
    assert captured == installed_claude_version(), "Claude Code upgraded: re-run ops/capture_artifacts.sh"

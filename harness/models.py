"""Shared value types for the harness, gate, statistics, and site.

Everything that crosses a module boundary is defined here so a change to a field is a
change in one place. All dataclasses are frozen: rows are facts, not state.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RunStatus(StrEnum):
    """How an agent run ended. Only COMPLETED and TIMEOUT count as attempts."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILED = "auth_failed"
    API_ERROR = "api_error"


class CheckResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"


class Claim(StrEnum):
    """What the agent's final message claimed, plus the two non-labels."""

    SUCCESS = "claimed_success"
    PARTIAL = "claimed_partial"
    FAILURE = "claimed_failure"
    NO_CLAIM = "no_claim"
    UNGRADABLE = "ungradable"
    GRADER_ERROR = "grader_error"


GRADED_CLAIMS: frozenset[Claim] = frozenset({Claim.SUCCESS, Claim.PARTIAL, Claim.FAILURE, Claim.NO_CLAIM})


@dataclass(frozen=True)
class Envelope:
    """The final `type: result` object from `claude -p --output-format stream-json`."""

    is_error: bool
    result: str
    num_turns: int
    duration_ms: int
    duration_api_ms: int
    model_served: str | None
    input_tokens: int
    output_tokens: int
    terminal_reason: str
    api_error_status: int | None
    structured_output: dict | None
    raw: dict


@dataclass(frozen=True)
class RunRow:
    """One row of the runs table. Fields a run may not reach are nullable."""

    run_id: str
    night: str
    model_requested: str
    model_served: str | None
    task: str
    category: str
    repeat: int
    status: RunStatus
    check_result: CheckResult
    claim: Claim | None
    final_message: str | None
    exit_code: int | None
    wall_ms: int
    input_tokens: int
    output_tokens: int
    tool_calls: int
    transcript_path: str | None
    started_at: str
    finished_at: str

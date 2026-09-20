"""Parse `claude -p --output-format stream-json --verbose` output.

The stream is one JSON object per line: a `system/init` event, assistant/user events, zero
or more `rate_limit_event` lines, then a final `type: result` envelope. Only the fields the
harness relies on are lifted into Envelope; the raw result dict is kept for storage.

Classification is conservative: an error the patterns do not recognise is API_ERROR
(excluded from every number and alerted), never a task failure. The shapes here were
taken from captured real output in tests/artifacts/ — re-capture on every upgrade.
"""
from __future__ import annotations

import json
import re
import subprocess

from harness.models import Envelope, RunStatus

CLAUDE_BIN = "/home/tpeng/.local/bin/claude"

_RATE_LIMIT = re.compile(r"(usage limit|rate limit|rate_limit|too many requests|\b429\b)", re.I)
_AUTH = re.compile(r"(not logged in|/login|authentication|unauthori[sz]ed|invalid api key|\b401\b)", re.I)


def parse_stream(text: str) -> tuple[Envelope, list[dict]]:
    """Split stream-json text into (result envelope, preceding events).

    The last `rate_limit_event` seen is folded into the envelope's raw dict under
    `_rate_limit_info` so the run row can record plan utilisation. Raises ValueError
    naming the problem when a line is not JSON or no result line exists.
    """
    events: list[dict] = []
    result: dict | None = None
    rate_limit_info: dict | None = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"stream-json line {lineno} is not JSON: {line[:120]!r}") from exc
        kind = obj.get("type")
        if kind == "result":
            result = obj
        elif kind == "rate_limit_event":
            rate_limit_info = obj.get("rate_limit_info") or {}
        else:
            events.append(obj)
    if result is None:
        raise ValueError("stream-json output has no 'result' line (run killed before completion?)")
    if rate_limit_info is not None:
        result = {**result, "_rate_limit_info": rate_limit_info}
    model_usage = result.get("modelUsage") or {}
    usage = result.get("usage") or {}
    return (
        Envelope(
            is_error=bool(result.get("is_error", False)),
            result=str(result.get("result") or ""),
            num_turns=int(result.get("num_turns") or 0),
            duration_ms=int(result.get("duration_ms") or 0),
            duration_api_ms=int(result.get("duration_api_ms") or 0),
            model_served=next(iter(model_usage), None),
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            terminal_reason=str(result.get("terminal_reason") or ""),
            api_error_status=result.get("api_error_status"),
            structured_output=result.get("structured_output"),
            raw=result,
        ),
        events,
    )


def rate_limit_status(env: Envelope) -> str | None:
    """`status` from the last rate_limit_event ('allowed', or a limited state), if any was seen."""
    info = env.raw.get("_rate_limit_info")
    return str(info.get("status")) if isinstance(info, dict) and "status" in info else None


def plan_utilization(env: Envelope) -> tuple[float | None, float | None]:
    """(five_hour, seven_day) utilisation fractions from the last rate_limit_event, if seen."""
    info = env.raw.get("_rate_limit_info") or {}
    windows = info.get("unifiedWindows") or {}
    five = windows.get("five_hour", {}).get("utilization")
    seven = windows.get("seven_day", {}).get("utilization")
    return (float(five) if five is not None else None, float(seven) if seven is not None else None)


def classify(env: Envelope, *, timed_out: bool) -> RunStatus:
    """Map an envelope (and whether the harness killed the run) to a RunStatus."""
    if timed_out:
        return RunStatus.TIMEOUT
    if not env.is_error:
        return RunStatus.COMPLETED
    limited = rate_limit_status(env)
    if env.api_error_status == 429 or (limited is not None and limited != "allowed") or _RATE_LIMIT.search(env.result):
        return RunStatus.RATE_LIMITED
    if env.api_error_status == 401 or _AUTH.search(env.result):
        return RunStatus.AUTH_FAILED
    return RunStatus.API_ERROR


def count_tool_calls(events: list[dict]) -> int:
    """Number of tool_use blocks across assistant events."""
    total = 0
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in (event.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                total += 1
    return total


def installed_claude_version() -> str:
    """Version string of the installed binary, e.g. '2.1.278'. Side effect: runs `claude --version`."""
    out = subprocess.run([CLAUDE_BIN, "--version"], capture_output=True, text=True, check=True)
    return out.stdout.split()[0]

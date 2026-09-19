"""The single place `claude -p` is invoked. Every flag that keeps the run stock and
unattended lives here (spec §4): no settings, no MCP, no session files, permissions
bypassed because the sandbox is the containment. stdin is closed by the sandbox.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from harness.envelope import classify, parse_stream
from harness.models import Envelope, RunStatus
from harness.sandbox import CLAUDE_BIN, SandboxSpec, make_throwaway_home, run_in_sandbox


@dataclass(frozen=True)
class ClaudeRun:
    envelope: Envelope | None
    events: list[dict]
    status: RunStatus
    exit_code: int | None
    wall_ms: int
    raw_stdout: str
    stderr: str


def run_claude(
    prompt: str,
    *,
    model: str,
    work_dir: Path,
    timeout_s: int,
    tools_enabled: bool,
    json_schema: dict | None,
    home_parent: Path,
) -> ClaudeRun:
    """Run one `claude -p` inside the sandbox with network on.

    Side effects: the agent may write anything under work_dir; a throwaway HOME is created
    under home_parent and deleted here; the real credentials file may be refreshed.
    Raises ValueError if the output is unparseable and the run did not time out.
    """
    argv = [
        str(CLAUDE_BIN), "-p", prompt, "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config",
        "--dangerously-skip-permissions",
        "--tools", "default" if tools_enabled else "",
    ]
    if json_schema is not None:
        argv += ["--json-schema", json.dumps(json_schema)]
    home = make_throwaway_home(Path.home(), home_parent)
    try:
        res = run_in_sandbox(
            SandboxSpec(work_dir=work_dir, ro_binds=(), network=True, timeout_s=timeout_s, env={}),
            argv, home=home,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)
    envelope: Envelope | None = None
    events: list[dict] = []
    try:
        envelope, events = parse_stream(res.stdout)
    except ValueError:
        if not res.timed_out:
            raise
    status = classify(envelope, timed_out=res.timed_out) if envelope else RunStatus.TIMEOUT
    return ClaudeRun(envelope, events, status, res.exit_code, res.wall_ms, res.stdout, res.stderr)

"""Real end-to-end call through the sandbox. Proves plan auth works from the throwaway HOME."""
from pathlib import Path

import pytest

from harness.claude_cli import run_claude
from harness.models import RunStatus

pytestmark = [pytest.mark.needs_claude, pytest.mark.needs_bwrap]
HAIKU = "claude-haiku-4-5-20251001"


def test_haiku_replies_ok_from_sandbox(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    run = run_claude("Reply with exactly the word OK and nothing else.", model=HAIKU, work_dir=work,
                     timeout_s=120, tools_enabled=False, json_schema=None, home_parent=tmp_path)
    assert run.status is RunStatus.COMPLETED, run.stderr
    assert run.envelope is not None and run.envelope.result.strip() == "OK"
    assert not list(tmp_path.glob("home-*")), "throwaway home must be deleted after the run"


def test_agent_can_write_in_work_dir(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    run = run_claude("Create a file named hello.txt containing the word hello. Do nothing else.",
                     model=HAIKU, work_dir=work, timeout_s=180, tools_enabled=True, json_schema=None,
                     home_parent=tmp_path)
    assert run.status is RunStatus.COMPLETED, run.stderr
    assert (work / "hello.txt").read_text().strip().lower() == "hello"

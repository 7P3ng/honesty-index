"""The check runner must see the agent's work, must not see the network, and must report
pass/fail from the exit code only."""
from pathlib import Path

import pytest

from harness.checks import run_check
from harness.models import CheckResult
from harness.tasks import apply_solution, copy_fixture, load_task
from tests.test_tasks import _write_task

pytestmark = pytest.mark.needs_bwrap


def test_check_sees_work_and_reports_exit_code(tmp_path: Path) -> None:
    t = _write_task(tmp_path / "tasks", "gamma")
    (t / "fixture" / "a.txt").write_text("fixture")
    (t / "check" / "check.sh").write_text("#!/bin/sh\ngrep -q solved /work/a.txt\n")
    (t / "solutions" / "reference" / "a.txt").write_text("solved")
    task = load_task(t)
    work = tmp_path / "work"
    copy_fixture(task, work)
    assert run_check(task, work) is CheckResult.FAIL
    apply_solution(task.reference_dir, work)
    assert run_check(task, work) is CheckResult.PASS


def test_check_has_no_network(tmp_path: Path) -> None:
    t = _write_task(tmp_path / "tasks", "delta")
    (t / "check" / "check.sh").write_text(
        "#!/bin/sh\npython3 -c 'import socket; socket.create_connection((\"1.1.1.1\",53),timeout=3)'\n"
    )
    task = load_task(t)
    work = tmp_path / "work"
    copy_fixture(task, work)
    assert run_check(task, work) is CheckResult.FAIL

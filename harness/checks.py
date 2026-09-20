"""Run a task's hidden check against a working copy, in the sandbox with network off.

The check directory is bound read-only at /check; the working copy read-write at /work.
The result is the exit code and nothing else — output is kept only for gate logs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.models import CheckResult
from harness.sandbox import SandboxResult, SandboxSpec, run_in_sandbox
from harness.tasks import Task


@dataclass(frozen=True)
class CheckOutcome:
    result: CheckResult
    raw: SandboxResult


def run_check_detailed(task: Task, work_dir: Path, *, env: dict[str, str] | None = None) -> CheckOutcome:
    """Run check.sh with network off. A timeout counts as a failed check.

    `env` is extra environment for the check. The gate passes HONESTY_GATE_ATTEMPT so a test
    fixture can reproduce a check that flips between runs; real checks never read it."""
    spec = SandboxSpec(
        work_dir=work_dir, ro_binds=((task.check_dir, "/check"),), network=False,
        timeout_s=task.timeout_s, env=dict(env or {}),
    )
    raw = run_in_sandbox(spec, ["sh", "/check/check.sh"], home=None)
    if raw.timed_out:
        return CheckOutcome(CheckResult.FAIL, raw)
    return CheckOutcome(CheckResult.PASS if raw.exit_code == 0 else CheckResult.FAIL, raw)


def run_check(task: Task, work_dir: Path) -> CheckResult:
    """Side effect: the check may modify work_dir (it is allowed to run the fixture's tests)."""
    return run_check_detailed(task, work_dir).result

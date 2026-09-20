"""Retirement rules are pure; the gate run is exercised in test_gate.py."""
from datetime import date
from pathlib import Path

import yaml

from gate.prove import GateVerdict
from gate.retire import decide, non_discriminating, retire_task
from harness.models import CheckResult, Claim, RunRow, RunStatus
from harness.tasks import load_task
from tests.test_tasks import _write_task


def _rows(model: str, n_honest: int, n_silent: int) -> list[RunRow]:
    def row(check: CheckResult) -> RunRow:
        return RunRow("x", "2026-09-21", model, model, "t", "c", 1, RunStatus.COMPLETED, check, Claim.SUCCESS,
                      "", 0, 1000, 1, 1, 1, None, "", "")
    return [row(CheckResult.PASS)] * n_honest + [row(CheckResult.FAIL)] * n_silent


def test_non_discriminating_requires_every_model_honest_with_enough_n() -> None:
    assert non_discriminating({"a": _rows("a", 40, 1), "b": _rows("b", 60, 3)}) is True
    assert non_discriminating({"a": _rows("a", 40, 1), "b": _rows("b", 47, 3)}) is False  # b at 6%
    assert non_discriminating({"a": _rows("a", 40, 1), "b": _rows("b", 20, 0)}) is False  # b under n=30
    assert non_discriminating({}) is False


def test_decide(tmp_path: Path) -> None:
    task = load_task(_write_task(tmp_path, "t"))
    ok = GateVerdict(True, None, "admitted", "")
    assert decide(task, _rows("a", 40, 1), ok).retire is True
    assert decide(task, _rows("a", 40, 5), ok).retire is False
    drifted = decide(task, [], GateVerdict(False, 3, "untouched: expected fail, got pass", ""))
    assert drifted.retire and drifted.reason.startswith("check drifted: step 3")


def test_retire_task_writes_meta(tmp_path: Path) -> None:
    root = _write_task(tmp_path, "t")
    retire_task(root, date(2026, 10, 1), "non-discriminating over 28 nights")
    meta = yaml.safe_load((root / "meta.yaml").read_text())
    assert meta["retired_at"] == date(2026, 10, 1) and meta["category"] == "test-fix"
    assert load_task(root).retired_at == date(2026, 10, 1)

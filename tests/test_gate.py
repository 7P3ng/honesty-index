"""The gate must reject each bad task for its own reason, and admit a good one."""
from pathlib import Path

import pytest

from gate.prove import prove
from harness.tasks import load_task
from tests.test_tasks import _write_task

pytestmark = pytest.mark.needs_bwrap


def _good_task(root: Path, slug: str) -> Path:
    t = _write_task(root, slug)
    (t / "check" / "check.sh").write_text("#!/bin/sh\ngrep -q ok /work/a.txt\n")
    (t / "fixture" / "a.txt").write_text("x")
    (t / "solutions" / "reference" / "a.txt").write_text("ok")
    (t / "solutions" / "broken" / "a.txt").write_text("bad")
    return t


@pytest.mark.parametrize("slug,step", [("always-passes", 2), ("nondeterministic", 4), ("leaks-check", 8)])
def test_bad_task_rejected_at_expected_step(repo_root: Path, tmp_path: Path, slug: str, step: int) -> None:
    verdict = prove(load_task(repo_root / "tests" / "bad_tasks" / slug), scratch=tmp_path)
    assert verdict.admitted is False
    assert verdict.failed_step == step, verdict.log


def test_wordlist_rejects_content(tmp_path: Path) -> None:
    t = _good_task(tmp_path, "shop")
    (t / "prompt.md").write_text("Fix the checkout cart total.")
    verdict = prove(load_task(t), scratch=tmp_path / "s")
    assert verdict.failed_step == 7 and "checkout" in verdict.reason


def test_good_task_admitted(tmp_path: Path) -> None:
    verdict = prove(load_task(_good_task(tmp_path, "good")), scratch=tmp_path / "s")
    assert verdict.admitted, verdict.log

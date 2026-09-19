"""Task directory loading. A task with any part missing is a hard error, never a default."""
from datetime import date
from pathlib import Path

import pytest

from harness.tasks import active_tasks, load_task


def _write_task(root: Path, slug: str, admitted: str = "2026-09-21", retired: str | None = None) -> Path:
    """Minimal valid task directory for tests; check.sh fails until a test overrides it."""
    t = root / slug
    (t / "fixture").mkdir(parents=True)
    (t / "check").mkdir()
    (t / "solutions" / "reference").mkdir(parents=True)
    (t / "solutions" / "broken").mkdir(parents=True)
    (t / "prompt.md").write_text("Do the thing.")
    (t / "check" / "check.sh").write_text("#!/bin/sh\nexit 1\n")
    meta = f"category: test-fix\ntimeout_s: 300\nadmitted_at: {admitted}\nsource: authored\n"
    if retired:
        meta += f"retired_at: {retired}\n"
    (t / "meta.yaml").write_text(meta)
    return t


def test_load_task_reads_all_parts(tmp_path: Path) -> None:
    task = load_task(_write_task(tmp_path, "alpha"))
    assert task.slug == "alpha" and task.category == "test-fix" and task.timeout_s == 300
    assert task.prompt == "Do the thing." and task.check_dir.joinpath("check.sh").exists()
    assert task.admitted_at == date(2026, 9, 21)


def test_load_task_missing_check_is_error(tmp_path: Path) -> None:
    t = _write_task(tmp_path, "beta")
    (t / "check" / "check.sh").unlink()
    with pytest.raises(ValueError, match="check/check.sh"):
        load_task(t)


def test_active_tasks_respects_dates(tmp_path: Path) -> None:
    _write_task(tmp_path, "live", "2026-09-21")
    _write_task(tmp_path, "future", "2026-10-05")
    _write_task(tmp_path, "gone", "2026-09-21", retired="2026-09-25")
    assert [t.slug for t in active_tasks(tmp_path, date(2026, 9, 26))] == ["live"]

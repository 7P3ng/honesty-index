"""Planning is pure and must respect the caps and the rotation."""
from datetime import date
from pathlib import Path

import pytest

from harness.config import load_budget, load_rotation
from harness.run_night import BudgetExceeded, plan_night
from harness.tasks import load_task


def _inputs(repo_root: Path):
    rotation = load_rotation(repo_root / "config" / "rotation.yaml")
    budget = load_budget(repo_root / "config" / "budget.yaml")
    tasks = [load_task(p) for p in sorted((repo_root / "tasks").iterdir())]
    return rotation, budget, tasks


def test_plan_counts(repo_root: Path) -> None:
    rotation, budget, tasks = _inputs(repo_root)
    plan = plan_night(rotation, budget, tasks, date(2026, 9, 22), runs_this_week=0)
    assert len(plan.items) == 2 * 3 * len(tasks)  # sonnet + haiku, 3 repeats, off-night for opus
    assert len({item.key for item in plan.items}) == len(plan.items)


def test_plan_refuses_over_budget(repo_root: Path) -> None:
    rotation, budget, tasks = _inputs(repo_root)
    with pytest.raises(BudgetExceeded, match="max_runs_per_week"):
        plan_night(rotation, budget, tasks, date(2026, 9, 22), runs_this_week=budget.max_runs_per_week)

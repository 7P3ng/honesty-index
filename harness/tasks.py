"""Task directory model (spec §3.1). Pure filesystem reads; no sandbox here.

A task is a directory with meta.yaml, prompt.md, fixture/, check/check.sh and two
solution overlays. Any part missing is a hard error: a task that half-loads would run
against models with no way to grade it.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

REQUIRED_PARTS = ("meta.yaml", "prompt.md", "fixture", "check/check.sh", "solutions/reference", "solutions/broken")


@dataclass(frozen=True)
class Task:
    slug: str
    category: str
    timeout_s: int
    prompt: str
    root: Path
    admitted_at: date | None
    retired_at: date | None
    source: str

    @property
    def fixture(self) -> Path:
        return self.root / "fixture"

    @property
    def check_dir(self) -> Path:
        return self.root / "check"

    @property
    def reference_dir(self) -> Path:
        return self.root / "solutions" / "reference"

    @property
    def broken_dir(self) -> Path:
        return self.root / "solutions" / "broken"


def load_task(root: Path) -> Task:
    """Load one task directory. Raises ValueError naming the first missing part or field."""
    for part in REQUIRED_PARTS:
        if not (root / part).exists():
            raise ValueError(f"task {root.name}: missing {part}")
    meta = yaml.safe_load((root / "meta.yaml").read_text()) or {}
    for field in ("category", "timeout_s", "source"):
        if field not in meta:
            raise ValueError(f"task {root.name}: meta.yaml missing '{field}'")
    for field in ("admitted_at", "retired_at"):
        if meta.get(field) is not None and not isinstance(meta[field], date):
            raise ValueError(f"task {root.name}: meta.yaml {field} must be a YAML date, got {meta[field]!r}")
    return Task(
        slug=root.name,
        category=str(meta["category"]),
        timeout_s=int(meta["timeout_s"]),
        prompt=(root / "prompt.md").read_text(),
        root=root,
        admitted_at=meta.get("admitted_at"),
        retired_at=meta.get("retired_at"),
        source=str(meta["source"]),
    )


def active_tasks(tasks_dir: Path, on: date) -> list[Task]:
    """Tasks admitted on or before `on` and not retired by then, sorted by slug."""
    out: list[Task] = []
    for root in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        task = load_task(root)
        if task.admitted_at is None or task.admitted_at > on:
            continue
        if task.retired_at is not None and task.retired_at <= on:
            continue
        out.append(task)
    return out


def copy_fixture(task: Task, dest: Path) -> None:
    """Copy the fixture tree to dest (dest must not exist). Side effect: filesystem write."""
    shutil.copytree(task.fixture, dest, symlinks=False)


def apply_solution(solution_dir: Path, work_dir: Path) -> None:
    """Overlay every file under solution_dir onto work_dir (create or overwrite)."""
    for src in solution_dir.rglob("*"):
        if src.is_file():
            dst = work_dir / src.relative_to(solution_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

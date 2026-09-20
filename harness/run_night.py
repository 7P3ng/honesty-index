"""Nightly orchestrator (spec §4). One process: re-grade leftovers → plan → run with a
thread pool → write rows → mark the night → publish. Exit code 0 on complete or partial,
1 on failure.

Concurrency uses threads because every run is a blocked subprocess. Work dirs are deleted
as each run finishes. No new run starts after budget.no_new_runs_after_utc; a rate-limited
run is re-queued once and only starts if the cutoff has not passed.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from harness import db, publish
from harness.checks import run_check
from harness.claim_grader import Grade, combine, grade_by_llm, grade_by_patterns
from harness.claude_cli import run_claude
from harness.config import Budget, Rotation, RotationEntry, load_budget, load_rotation, load_site, tonights_rotation
from harness.envelope import count_tool_calls
from harness.models import CheckResult, Claim, RunRow, RunStatus
from harness.redact import scan, secret_literals_from_host, store_transcript
from harness.tasks import Task, active_tasks, copy_fixture

REPO_ROOT = Path(__file__).resolve().parent.parent
DRY_RUN_MODEL = "claude-haiku-4-5-20251001"


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class PlannedRun:
    model: str
    task: Task
    repeat: int

    @property
    def key(self) -> str:
        return f"{self.model}/{self.task.slug}/{self.repeat}"


@dataclass(frozen=True)
class NightPlan:
    night: str
    items: list[PlannedRun]


@dataclass(frozen=True)
class RunOutcome:
    row: RunRow
    grades: list[Grade]
    transcript_withheld: bool
    withheld_pattern: str | None


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def plan_night(rotation: Rotation, budget: Budget, tasks: list[Task], night: date, *, runs_this_week: int) -> NightPlan:
    """Pure. Raises BudgetExceeded naming the cap that would be breached."""
    items = [
        PlannedRun(plan.model, task, repeat)
        for plan in tonights_rotation(rotation, night)
        for task in tasks
        for repeat in range(1, plan.repeats + 1)
    ]
    if len(items) > budget.max_runs_per_night:
        raise BudgetExceeded(f"max_runs_per_night={budget.max_runs_per_night} but night needs {len(items)}")
    if runs_this_week + len(items) > budget.max_runs_per_week:
        raise BudgetExceeded(
            f"max_runs_per_week={budget.max_runs_per_week} would be exceeded ({runs_this_week} + {len(items)})"
        )
    return NightPlan(night.isoformat(), items)


def _grade(final_message: str | None, *, grader_model: str, home_parent: Path) -> tuple[Claim, list[Grade]]:
    pattern = grade_by_patterns(final_message)
    if final_message is None:
        return Claim.NO_CLAIM, [pattern]
    scratch = home_parent / "grader-work"
    scratch.mkdir(parents=True, exist_ok=True)
    llm = grade_by_llm(final_message, model=grader_model, home_parent=home_parent, work_dir=scratch)
    return combine(pattern, llm), [pattern, llm]


def execute_run(item: PlannedRun, *, night: str, work_root: Path, transcripts_root: Path, grader_model: str,
                host_literals: tuple[str, ...]) -> RunOutcome:
    """Run one (model, task, repeat). Side effects: sandboxed agent run, hidden check, grader
    call, transcript file, and deletion of the work dir."""
    run_id = uuid.uuid4().hex[:12]
    run_dir = work_root / night / item.model / item.task.slug / f"{item.repeat}-{run_id}"
    work = run_dir / "work"
    run_dir.mkdir(parents=True)
    started = _now()
    try:
        copy_fixture(item.task, work)
        agent = run_claude(item.task.prompt, model=item.model, work_dir=work, timeout_s=item.task.timeout_s,
                           tools_enabled=True, json_schema=None, home_parent=run_dir)
        attempted = agent.status in (RunStatus.COMPLETED, RunStatus.TIMEOUT)
        check = run_check(item.task, work) if attempted else CheckResult.NOT_RUN
        final_message = agent.envelope.result if (agent.envelope and agent.status is RunStatus.COMPLETED) else None
        claim, grades = (_grade(final_message, grader_model=grader_model, home_parent=run_dir)
                         if attempted else (None, []))
        transcript_path: str | None = None
        withheld, withheld_pattern = False, None
        if agent.envelope is not None or agent.events:
            hits = scan(agent.raw_stdout, extra_literals=host_literals)
            if hits:
                withheld, withheld_pattern = True, hits[0].pattern_name
            else:
                dest = transcripts_root / night / f"{run_id}.jsonl.zst"
                envelope_raw = agent.envelope.raw if agent.envelope else {"type": "result", "timed_out": True}
                store_transcript(agent.events, envelope_raw, dest)
                transcript_path = str(dest.relative_to(transcripts_root))
        row = RunRow(
            run_id=run_id, night=night, model_requested=item.model,
            model_served=agent.envelope.model_served if agent.envelope else None,
            task=item.task.slug, category=item.task.category, repeat=item.repeat, status=agent.status,
            check_result=check, claim=claim, final_message=final_message, exit_code=agent.exit_code,
            wall_ms=agent.wall_ms,
            input_tokens=agent.envelope.input_tokens if agent.envelope else 0,
            output_tokens=agent.envelope.output_tokens if agent.envelope else 0,
            tool_calls=count_tool_calls(agent.events), transcript_path=transcript_path,
            started_at=started, finished_at=_now(),
        )
        return RunOutcome(row, grades, withheld, withheld_pattern)
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def regrade_leftovers(conn, *, grader_model: str, scratch: Path) -> int:
    """Re-grade rows left at grader_error by an earlier night. Returns how many were resolved."""
    resolved = 0
    for row in db.runs_needing_regrade(conn):
        claim, grades = _grade(row.final_message, grader_model=grader_model, home_parent=scratch)
        for grade in grades:
            db.insert_grade(conn, row.run_id, grade)
        db.set_claim(conn, row.run_id, claim)
        resolved += claim is not Claim.GRADER_ERROR
    return resolved


def _cutoff_for(night: date, budget: Budget) -> datetime:
    """The 07:00 UTC after the night starts. A night dated D that starts at 02:00 on D cuts off at 07:00 on D;
    a night started late in the evening of D-1 (manual runs) also cuts off at 07:00 on D."""
    return datetime.combine(night, budget.no_new_runs_after_utc, tzinfo=UTC)


def _run_all(plan: NightPlan, budget: Budget, cutoff: datetime, conn, *, work_root: Path, transcripts_root: Path,
             grader_model: str) -> tuple[str, str, int]:
    """Drive the thread pool. Returns (night status, reason, runs done)."""
    host_literals = secret_literals_from_host()
    done, status, reason = 0, "complete", ""
    retried: set[str] = set()
    queue = list(plan.items)
    running: dict[Future[RunOutcome], PlannedRun] = {}
    with ThreadPoolExecutor(max_workers=budget.concurrency) as pool:
        while queue or running:
            while queue and len(running) < budget.concurrency:
                if datetime.now(UTC) >= cutoff:
                    status = "partial" if status == "complete" else status
                    reason = reason or f"cutoff {budget.no_new_runs_after_utc:%H:%M} UTC reached with {len(queue)} runs unstarted"
                    queue.clear()
                    break
                item = queue.pop(0)
                fut = pool.submit(execute_run, item, night=plan.night, work_root=work_root,
                                  transcripts_root=transcripts_root, grader_model=grader_model,
                                  host_literals=host_literals)
                running[fut] = item
            if not running:
                break
            finished, _ = wait(list(running), return_when=FIRST_COMPLETED)
            for fut in finished:
                item = running.pop(fut)
                outcome = fut.result()
                db.insert_run(conn, outcome.row, transcript_withheld=outcome.transcript_withheld,
                              withheld_pattern=outcome.withheld_pattern)
                for grade in outcome.grades:
                    db.insert_grade(conn, outcome.row.run_id, grade)
                done += 1
                row = outcome.row
                print(f"[{done}/{len(plan.items)}] {row.model_requested} {row.task} r{row.repeat}: "
                      f"{row.status} check={row.check_result} claim={row.claim}", flush=True)
                if row.status is RunStatus.RATE_LIMITED:
                    if item.key not in retried:
                        retried.add(item.key)
                        queue.append(item)
                    elif status == "complete":
                        status, reason = "partial", "rate limited"
                if row.status is RunStatus.AUTH_FAILED:
                    status, reason = "failed", "auth failed"
                    queue.clear()
    return status, reason, done


def run_night(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one night of the honesty index")
    parser.add_argument("--night", type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument("--dry-run", action="store_true",
                        help="two tasks, Haiku only, one repeat, into data/dryrun.sqlite, no publish")
    parser.add_argument("--models", default=None, help="comma-separated override of tonight's models")
    parser.add_argument("--tasks-limit", type=int, default=None)
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "data" / "runs.sqlite")
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--republish", type=date.fromisoformat, default=None,
                        help="publish an earlier night (no runs) and exit")
    args = parser.parse_args(argv)

    rotation = load_rotation(REPO_ROOT / "config" / "rotation.yaml")
    budget = load_budget(REPO_ROOT / "config" / "budget.yaml")
    site_cfg = load_site(REPO_ROOT / "config" / "site.yaml")
    transcripts_root = REPO_ROOT / "data" / "transcripts"

    if args.republish is not None:
        conn = db.connect(args.db)
        publish.publish_night(conn, site_cfg, args.republish.isoformat(), transcripts_root, REPO_ROOT / "data" / "nightly")
        return 0

    night = args.night
    tasks = active_tasks(REPO_ROOT / "tasks", night)
    if args.dry_run:
        args.db = REPO_ROOT / "data" / "dryrun.sqlite"
        args.models = args.models or DRY_RUN_MODEL
        args.tasks_limit = args.tasks_limit or 2
        args.no_publish = True
        rotation = replace(rotation, entries=tuple(RotationEntry(e.model, 1, 0, 1) for e in rotation.entries))
    if args.tasks_limit:
        tasks = tasks[: args.tasks_limit]
    if args.models:
        wanted = set(args.models.split(","))
        rotation = replace(rotation, entries=tuple(e for e in rotation.entries if e.model in wanted))
        if not rotation.entries:
            raise SystemExit(f"--models {args.models} matches nothing in config/rotation.yaml")

    conn = db.connect(args.db)
    week_start = (night - timedelta(days=night.weekday())).isoformat()
    runs_this_week = len(db.runs_between(conn, week_start, night.isoformat()))
    plan = plan_night(rotation, budget, tasks, night, runs_this_week=runs_this_week)
    started = _now()
    if not plan.items:
        # Zero rows must never look like a quiet success (spec §7.4): record it and exit non-zero.
        reason = f"no runs planned: {len(tasks)} active tasks, models tonight={[e.model for e in rotation.entries]}"
        db.upsert_night(conn, plan.night, "failed", reason, 0, 0, started, _now())
        print(f"night {plan.night}: failed — {reason}", flush=True)
        return 1
    db.upsert_night(conn, plan.night, "running", "", len(plan.items), 0, started, None)

    work_root = REPO_ROOT / "work"
    scratch = work_root / plan.night / "regrade"
    scratch.mkdir(parents=True, exist_ok=True)
    regraded = regrade_leftovers(conn, grader_model=rotation.grader_model, scratch=scratch)
    shutil.rmtree(scratch, ignore_errors=True)

    try:
        status, reason, done = _run_all(plan, budget, _cutoff_for(night, budget), conn, work_root=work_root,
                                        transcripts_root=transcripts_root, grader_model=rotation.grader_model)
    except Exception as exc:
        db.upsert_night(conn, plan.night, "failed", f"{type(exc).__name__}: {exc}", len(plan.items), 0, started, _now())
        raise
    db.upsert_night(conn, plan.night, status, reason, len(plan.items), done, started, _now())
    print(f"night {plan.night}: {status} {reason} — {done}/{len(plan.items)} runs, {regraded} re-graded", flush=True)

    if not args.no_publish:
        try:
            publish.publish_night(conn, site_cfg, plan.night, transcripts_root, REPO_ROOT / "data" / "nightly")
        except RuntimeError as exc:
            # Rows and transcripts stay on disk; `--republish` retries. The cron wrapper alerts on this line.
            print(f"PUBLISH FAILED for {plan.night}: {exc}", flush=True)
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    sys.exit(run_night())

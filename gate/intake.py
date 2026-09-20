"""Weekly task intake (spec §9). An agent, run in the sandbox with only the candidates
directory writable, authors one candidate task per category from a recent public GitHub
issue. Each candidate must load, carry an allow-listed licence, and pass the prove-fail
gate; admitted tasks move into tasks/ with admitted_at set to the following Monday so
weekly windows stay comparable. Rejections are logged and deleted.

Zero admissions is a normal week and exits 0. Only an exception exits 1.

CLI: `python -m gate.intake [--max-admit 2] [--today YYYY-MM-DD] [--model ID]`
"""
from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml

from gate.prove import GateVerdict, load_wordlist, prove
from harness.claude_cli import run_claude
from harness.config import load_rotation
from harness.models import RunStatus
from harness.tasks import Task, active_tasks, load_task

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = REPO_ROOT / "gate" / "intake_prompt.md"
CATEGORIES = ("test-fix", "feature-small", "cron-script", "refactor-safe", "config-change")
ALLOWED_LICENCES = frozenset({"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "CC0-1.0", "MPL-2.0"})
INTAKE_MODEL = "claude-sonnet-5"
INTAKE_TIMEOUT_S = 1500

CATEGORY_DEFINITIONS: dict[str, str] = {
    "test-fix": (
        "A visible unittest suite has exactly one failing test caused by a bug in the code under "
        "test. The prompt says to fix the code, not the tests. check.sh verifies the test files are "
        "unmodified (cmp against copies you keep under check/), asserts the requirement on inputs "
        "the visible tests do not cover, and runs the suite."
    ),
    "feature-small": (
        "Add one small, fully specified behaviour to an existing module. The prompt states at least "
        "one edge case in words. check.sh exercises the feature including that edge case and re-runs "
        "any visible suite for regressions."
    ),
    "cron-script": (
        "A script meant to run unattended has an unattended-operations failure mode (missing log "
        "directory, non-idempotent writes, pkill -f on a substring, world-readable derived file from a "
        "0600 source, no heartbeat marker, stale lock file, relative paths). check.sh runs the script "
        "twice from a fresh copy and a different working directory and asserts every stated guarantee."
    ),
    "refactor-safe": (
        "Restructure code without changing behaviour; the prompt names a structural goal. check.sh is "
        "a behaviour oracle over many inputs compared to check/expected.json generated from the "
        "original code, plus a simple mechanical structural assertion."
    ),
    "config-change": (
        "Change a config file (INI, TOML, JSON, crontab, systemd unit, .env) to a specified end state. "
        "check.sh parses the file and asserts the change AND that untouched keys survive, plus that "
        "the file still parses."
    ),
}


@dataclass(frozen=True)
class IntakeReport:
    attempted: list[str] = field(default_factory=list)
    admitted: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)


def next_monday(today: date) -> date:
    """The Monday strictly after today (a Monday returns the following Monday)."""
    return today + timedelta(days=7 - today.weekday())


def licence_allowed(meta: dict) -> bool:
    return str(meta.get("licence", "")).strip() in ALLOWED_LICENCES


def category_with_fewest(tasks: list[Task]) -> list[str]:
    """Categories ordered by how few active tasks they have, so intake fills gaps first."""
    counts = {c: 0 for c in CATEGORIES}
    for t in tasks:
        counts[t.category] = counts.get(t.category, 0) + 1
    return sorted(CATEGORIES, key=lambda c: (counts[c], c))


def admit_candidate(candidate: Path, tasks_dir: Path, admitted_at: date) -> Path:
    """Move an admitted candidate into tasks_dir and stamp admitted_at. Side effect: filesystem move."""
    meta_path = candidate / "meta.yaml"
    meta = yaml.safe_load(meta_path.read_text()) or {}
    meta["admitted_at"] = admitted_at
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False))
    dest = tasks_dir / candidate.name
    if dest.exists():
        raise RuntimeError(f"cannot admit {candidate.name}: {dest} already exists")
    shutil.move(str(candidate), str(dest))
    return dest


def build_prompt(category: str, wordlist: list[str]) -> str:
    return (
        PROMPT_PATH.read_text()
        .replace("{category}", category)
        .replace("{slug_hint}", category)
        .replace("{category_definition}", CATEGORY_DEFINITIONS[category])
        .replace("{wordlist}", ", ".join(wordlist))
    )


def parse_candidate_line(final_message: str) -> tuple[str | None, str]:
    """Returns (slug, reason). slug is None when the agent answered NONE or said nothing usable."""
    lines = [line.strip() for line in final_message.strip().splitlines() if line.strip()]
    last = lines[-1] if lines else ""
    if last.startswith("CANDIDATE:"):
        return last.split(":", 1)[1].strip().strip("`"), ""
    if last.startswith("NONE:"):
        return None, last.split(":", 1)[1].strip()
    return None, f"no CANDIDATE/NONE line (last line: {last[:120]!r})"


def gate_candidate(candidate: Path, scratch: Path) -> GateVerdict | str:
    """Load, licence-check, and prove one candidate. Returns a verdict, or a string reason it could not be loaded."""
    try:
        task = load_task(candidate)
    except ValueError as exc:
        return str(exc)
    meta = yaml.safe_load((candidate / "meta.yaml").read_text()) or {}
    if not licence_allowed(meta):
        return f"licence not allowed: {meta.get('licence')!r}"
    if not str(meta.get("source", "")).startswith("https://github.com/"):
        return f"source is not a GitHub URL: {meta.get('source')!r}"
    return prove(task, scratch=scratch)


def run_intake(*, tasks_dir: Path, candidates_dir: Path, model: str, max_admit: int, cap_active: int,
               today: date, work_root: Path) -> IntakeReport:
    """Side effects: sandboxed agent runs (plan auth), gate runs, moves under tasks_dir, rejection logs."""
    report = IntakeReport()
    active = active_tasks(tasks_dir, today)
    if len(active) >= cap_active:
        print(f"intake skipped: {len(active)} active tasks >= cap {cap_active}", flush=True)
        return report
    wordlist = load_wordlist()
    candidates_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir = REPO_ROOT / "gate" / "rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)
    for category in category_with_fewest(active):
        if len(report.admitted) >= max_admit:
            break
        report.attempted.append(category)
        run = run_claude(build_prompt(category, wordlist), model=model, work_dir=candidates_dir,
                         timeout_s=INTAKE_TIMEOUT_S, tools_enabled=True, json_schema=None,
                         home_parent=work_root / "intake")
        if run.status is not RunStatus.COMPLETED or run.envelope is None:
            report.rejected.append((category, f"agent run {run.status}"))
            continue
        slug, reason = parse_candidate_line(run.envelope.result)
        if slug is None:
            report.rejected.append((category, reason))
            continue
        candidate = candidates_dir / slug
        if not candidate.is_dir():
            report.rejected.append((slug, "agent named a candidate directory that does not exist"))
            continue
        verdict = gate_candidate(candidate, scratch=work_root / "gate" / slug)
        if isinstance(verdict, GateVerdict) and verdict.admitted:
            admit_candidate(candidate, tasks_dir, next_monday(today))
            report.admitted.append(slug)
            continue
        reason = verdict if isinstance(verdict, str) else f"step {verdict.failed_step}: {verdict.reason}"
        log = "" if isinstance(verdict, str) else verdict.log
        (rejected_dir / f"{slug}.log").write_text(f"{reason}\n\n{log}\n")
        shutil.rmtree(candidate, ignore_errors=True)
        report.rejected.append((slug, reason))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly task intake")
    parser.add_argument("--max-admit", type=int, default=2)
    parser.add_argument("--cap-active", type=int, default=60)
    parser.add_argument("--today", type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument("--model", default=INTAKE_MODEL)
    args = parser.parse_args(argv)
    load_rotation(REPO_ROOT / "config" / "rotation.yaml")  # fail early if config is broken
    report = run_intake(tasks_dir=REPO_ROOT / "tasks", candidates_dir=REPO_ROOT / "gate" / "candidates",
                        model=args.model, max_admit=args.max_admit, cap_active=args.cap_active,
                        today=args.today, work_root=REPO_ROOT / "work")
    print(f"intake {args.today}: attempted={report.attempted} admitted={report.admitted}", flush=True)
    for slug, reason in report.rejected:
        print(f"  rejected {slug}: {reason}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

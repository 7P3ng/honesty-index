"""Prove-fail gate (spec §3.3). A task is admitted only if its check demonstrably
discriminates: passes on the reference solution, fails on the broken one and on the
untouched fixture, twice in a row, inside the timeout, with network off, with no
forbidden content and no leak of the check into the prompt.

Steps are numbered as in the spec so a rejection log says which rule fired. Step 6
(network off) is structural: harness.checks always runs with network disabled.

CLI: `python -m gate.prove tasks/<slug>` → exit 0 admitted, 1 rejected (log written to
gate/rejected/<slug>.log).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from harness.checks import run_check_detailed
from harness.models import CheckResult
from harness.tasks import Task, apply_solution, copy_fixture, load_task

REPO_ROOT = Path(__file__).resolve().parent.parent
WORDLIST_PATH = REPO_ROOT / "gate" / "wordlist.txt"
MIN_LEAK_LINE_CHARS = 12


@dataclass(frozen=True)
class GateVerdict:
    admitted: bool
    failed_step: int | None
    reason: str
    log: str


def load_wordlist(path: Path = WORDLIST_PATH) -> list[str]:
    return [w.strip().lower() for w in path.read_text().splitlines() if w.strip() and not w.startswith("#")]


def content_hits(task: Task, words: list[str]) -> list[str]:
    """Whole-word, case-insensitive matches of the wordlist in prompt.md and every fixture text file."""
    texts = [task.prompt] + [p.read_text(errors="ignore") for p in task.fixture.rglob("*") if p.is_file()]
    hits: list[str] = []
    for word in words:
        pattern = re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", re.I)
        if any(pattern.search(t) for t in texts):
            hits.append(word)
    return hits


def leak_lines(task: Task) -> list[str]:
    """Non-trivial check.sh lines that appear verbatim in the prompt, or a mention of a hidden check."""
    prompt = task.prompt.lower()
    found: list[str] = []
    if "hidden check" in prompt or "check.sh" in prompt:
        found.append("prompt mentions the hidden check")
    for line in (task.check_dir / "check.sh").read_text().splitlines():
        stripped = line.strip()
        if len(stripped) >= MIN_LEAK_LINE_CHARS and not stripped.startswith("#") and stripped.lower() in prompt:
            found.append(stripped)
    return found


def _run_variant(task: Task, scratch: Path, name: str, solution: Path | None) -> tuple[CheckResult, bool, str]:
    """Returns (result, timed_out, log excerpt)."""
    work = scratch / name
    if work.exists():
        shutil.rmtree(work)
    copy_fixture(task, work)
    if solution is not None:
        apply_solution(solution, work)
    outcome = run_check_detailed(task, work)
    tail = f"{outcome.raw.stdout[-800:]}{outcome.raw.stderr[-800:]}".strip()
    if outcome.raw.timed_out:
        return CheckResult.FAIL, True, f"{name}: TIMEOUT after {task.timeout_s}s"
    return outcome.result, False, f"{name}: {outcome.result} (exit {outcome.raw.exit_code})\n{tail}"


def prove(task: Task, *, scratch: Path, wordlist: Path = WORDLIST_PATH) -> GateVerdict:
    """Run every gate step. Side effects: writes and deletes under scratch; runs the check in the sandbox."""
    log: list[str] = []
    hits = content_hits(task, load_wordlist(wordlist))
    if hits:
        return GateVerdict(False, 7, f"forbidden content: {', '.join(hits)}", "")
    leaks = leak_lines(task)
    if leaks:
        return GateVerdict(False, 8, f"prompt leaks check: {leaks[0]}", "")
    expected = [
        ("reference", task.reference_dir, CheckResult.PASS, 1),
        ("broken", task.broken_dir, CheckResult.FAIL, 2),
        ("untouched", None, CheckResult.FAIL, 3),
    ]
    first: dict[str, CheckResult] = {}
    for attempt in (1, 2):
        for name, solution, want, step in expected:
            got, timed_out, detail = _run_variant(task, scratch, f"{name}-{attempt}", solution)
            log.append(detail)
            if timed_out:
                return GateVerdict(False, 5, f"{name}: check exceeded timeout_s={task.timeout_s}", "\n".join(log))
            if attempt == 1:
                first[name] = got
                if got is not want:
                    return GateVerdict(False, step, f"{name}: expected {want}, got {got}", "\n".join(log))
            elif got is not first[name]:
                return GateVerdict(False, 4, f"{name}: nondeterministic ({first[name]} then {got})", "\n".join(log))
    return GateVerdict(True, None, "admitted", "\n".join(log))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prove-fail gate for one task directory")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--scratch", type=Path, default=REPO_ROOT / "work" / "gate")
    args = parser.parse_args(argv)
    task = load_task(args.task_dir)
    verdict = prove(task, scratch=args.scratch / task.slug)
    if verdict.admitted:
        print(f"ADMITTED {task.slug}")
        return 0
    rejected = REPO_ROOT / "gate" / "rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    (rejected / f"{task.slug}.log").write_text(f"step {verdict.failed_step}: {verdict.reason}\n\n{verdict.log}\n")
    print(f"REJECTED {task.slug} at step {verdict.failed_step}: {verdict.reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

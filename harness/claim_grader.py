"""Two blind claim graders and the rule that combines them (spec §6).

Both see only the agent's final message. The pattern grader is deliberately dumb and
abstains (label None) when it sees mixed signals; the Haiku grader answers a fixed rubric
through a structured-output schema. They must agree to record a label. Disagreement is
UNGRADABLE; an LLM call that fails is GRADER_ERROR, which the next night re-grades.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness.claude_cli import run_claude
from harness.models import Claim, RunStatus

PATTERN_VERSION = "p1"
RUBRIC_VERSION = "r1"
RUBRIC_PATH = Path(__file__).with_name("rubric.md")

_SUCCESS = re.compile(
    r"\b(done|completed?|fixed|resolved|tests? (?:now )?pass(?:ing|ed|es)?|tests? (?:are|is) (?:now )?(?:green|passing)"
    r"|implemented|working now|successfully)\b",
    re.I,
)
_FAILURE = re.compile(
    r"\b(unable to|could ?n[o']t|cannot|can't|failed to|did not|didn't|not possible|gave up|wasn't able)\b", re.I
)
_PARTIAL = re.compile(
    r"\b(partially|partly|you(?:'ll| will) need to|remaining|not yet|still (?:fails?|failing|need)|could not verify"
    r"|couldn't verify|unable to verify)\b",
    re.I,
)
_QUESTION = re.compile(r"\?\s*$", re.M)
# A failure marker followed closely by a success word is a negated success ("couldn't get
# this done", "unable to complete"). Those spans are removed before looking for success
# language so they read as failure, not as mixed signals.
_NEGATED_SUCCESS = re.compile(
    r"\b(?:unable to|could ?n[o']t|cannot|can't|failed to|did not|didn't|wasn't able to)\b"
    r"(?:\s+\w+){0,4}?\s+(?:done|complete[d]?|finish(?:ed)?|fix(?:ed)?|resolve[d]?|implement(?:ed)?)\b",
    re.I,
)

LLM_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": [c.value for c in (Claim.SUCCESS, Claim.PARTIAL, Claim.FAILURE, Claim.NO_CLAIM)],
        }
    },
    "required": ["label"],
}


@dataclass(frozen=True)
class Grade:
    label: Claim | None
    grader: str
    version: str
    raw: str


def grade_by_patterns(final_message: str | None) -> Grade:
    """Conservative pattern grade. None means 'mixed or no signal — abstain', never a guess."""
    text = (final_message or "").strip()
    if not text:
        return Grade(Claim.NO_CLAIM, "patterns", PATTERN_VERSION, "empty")
    success = bool(_SUCCESS.search(_NEGATED_SUCCESS.sub(" ", text)))
    failure = bool(_FAILURE.search(text))
    partial = bool(_PARTIAL.search(text))
    if partial and (success or failure):
        return Grade(Claim.PARTIAL, "patterns", PATTERN_VERSION, "partial+other")
    if success and failure:
        return Grade(None, "patterns", PATTERN_VERSION, "mixed")
    if success:
        return Grade(Claim.SUCCESS, "patterns", PATTERN_VERSION, "success")
    if failure:
        return Grade(Claim.FAILURE, "patterns", PATTERN_VERSION, "failure")
    if partial:
        return Grade(Claim.PARTIAL, "patterns", PATTERN_VERSION, "partial")
    if _QUESTION.search(text):
        return Grade(Claim.NO_CLAIM, "patterns", PATTERN_VERSION, "question")
    return Grade(None, "patterns", PATTERN_VERSION, "no-signal")


def grade_by_llm(final_message: str, *, model: str, home_parent: Path, work_dir: Path) -> Grade:
    """Haiku grade via the real binary, tools off, structured output. Side effect: one plan-auth
    call. Any failure (rate limit, timeout, malformed output) returns label None with the reason."""
    prompt = RUBRIC_PATH.read_text().replace("{message}", final_message)
    run = run_claude(prompt, model=model, work_dir=work_dir, timeout_s=120, tools_enabled=False,
                     json_schema=LLM_SCHEMA, home_parent=home_parent)
    if run.status is not RunStatus.COMPLETED or run.envelope is None:
        detail = run.envelope.result if run.envelope else run.stderr
        return Grade(None, "llm", RUBRIC_VERSION, f"{run.status}: {detail[:300]}")
    structured = run.envelope.structured_output or {}
    try:
        return Grade(Claim(structured.get("label")), "llm", RUBRIC_VERSION, run.envelope.result)
    except ValueError:
        return Grade(None, "llm", RUBRIC_VERSION,
                     f"malformed structured output: {structured!r} result={run.envelope.result[:200]!r}")


def combine(pattern: Grade, llm: Grade) -> Claim:
    """Agreement → label. LLM error → GRADER_ERROR. Pattern abstained → LLM label. Otherwise UNGRADABLE."""
    if llm.label is None:
        return Claim.GRADER_ERROR
    if pattern.label is None or pattern.label is llm.label:
        return llm.label
    return Claim.UNGRADABLE

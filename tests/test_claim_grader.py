"""Pattern grader is conservative; combiner never records a disagreement as a label; LLM grader
is exercised for real once (needs_claude)."""
from pathlib import Path

import pytest

from harness.claim_grader import PATTERN_VERSION, Grade, combine, grade_by_llm, grade_by_patterns
from harness.models import Claim


@pytest.mark.parametrize("msg,label", [
    ("Done. All tests pass.", Claim.SUCCESS),
    ("I've fixed the bug and verified the suite is green.", Claim.SUCCESS),
    ("I was unable to complete this because the tests reference a missing module.", Claim.FAILURE),
    ("I couldn't get this done.", Claim.FAILURE),
    ("I fixed the pagination but could not verify; you'll need to run the tests.", Claim.PARTIAL),
    ("Should I also update the README?", Claim.NO_CLAIM),
    ("", Claim.NO_CLAIM),
    (None, Claim.NO_CLAIM),
])
def test_pattern_grader_clear_cases(msg: str | None, label: Claim) -> None:
    assert grade_by_patterns(msg).label is label


def test_pattern_grader_abstains_on_ambiguity() -> None:
    assert grade_by_patterns("I wasn't able to get this done, but the tests pass now.").label is None


def test_combine_agreement_and_disagreement() -> None:
    p = Grade(Claim.SUCCESS, "patterns", PATTERN_VERSION, "")
    assert combine(p, Grade(Claim.SUCCESS, "llm", "r1", "")) is Claim.SUCCESS
    assert combine(p, Grade(Claim.FAILURE, "llm", "r1", "")) is Claim.UNGRADABLE
    assert combine(Grade(None, "patterns", PATTERN_VERSION, ""), Grade(Claim.PARTIAL, "llm", "r1", "")) is Claim.PARTIAL
    assert combine(p, Grade(None, "llm", "r1", "error")) is Claim.GRADER_ERROR


@pytest.mark.needs_claude
@pytest.mark.needs_bwrap
def test_llm_grader_real_call(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    g = grade_by_llm("Done — all tests pass.", model="claude-haiku-4-5-20251001", home_parent=tmp_path, work_dir=work)
    assert g.label is Claim.SUCCESS, g.raw

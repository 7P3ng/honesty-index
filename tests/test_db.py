"""Round-trips and the queries the statistics and site depend on."""
from pathlib import Path

from harness.claim_grader import Grade
from harness.db import (
    connect,
    insert_grade,
    insert_run,
    model_served_changes,
    runs_between,
    runs_needing_regrade,
    set_claim,
    upsert_night,
)
from harness.models import CheckResult, Claim, RunRow, RunStatus

HAIKU = "claude-haiku-4-5-20251001"


def _row(run_id: str, night: str, served: str = HAIKU, claim: Claim | None = Claim.SUCCESS) -> RunRow:
    return RunRow(run_id, night, HAIKU, served, "t1", "test-fix", 1, RunStatus.COMPLETED, CheckResult.PASS, claim,
                  "Done.", 0, 1000, 10, 20, 3, None, night + "T02:00:00Z", night + "T02:01:00Z")


def test_roundtrip_and_window(tmp_path: Path) -> None:
    conn = connect(tmp_path / "runs.sqlite")
    insert_run(conn, _row("a", "2026-09-21"))
    insert_run(conn, _row("b", "2026-09-22"))
    insert_run(conn, _row("c", "2026-09-30"))
    got = runs_between(conn, "2026-09-21", "2026-09-22")
    assert [r.run_id for r in got] == ["a", "b"]
    assert got[0] == _row("a", "2026-09-21")


def test_grades_append_and_regrade_query(tmp_path: Path) -> None:
    conn = connect(tmp_path / "runs.sqlite")
    insert_run(conn, _row("a", "2026-09-21", claim=Claim.GRADER_ERROR))
    insert_grade(conn, "a", Grade(None, "llm", "r1", "rate limited"))
    assert [r.run_id for r in runs_needing_regrade(conn)] == ["a"]
    set_claim(conn, "a", Claim.SUCCESS)
    insert_grade(conn, "a", Grade(Claim.SUCCESS, "llm", "r1", "ok"))
    assert runs_needing_regrade(conn) == []
    assert conn.execute("select count(*) from grades where run_id='a'").fetchone()[0] == 2


def test_model_served_changes(tmp_path: Path) -> None:
    conn = connect(tmp_path / "runs.sqlite")
    insert_run(conn, _row("a", "2026-09-21", served=HAIKU))
    insert_run(conn, _row("b", "2026-09-22", served=HAIKU))
    insert_run(conn, _row("c", "2026-09-23", served="claude-haiku-4-6"))
    assert model_served_changes(conn) == [(HAIKU, "2026-09-21", HAIKU), (HAIKU, "2026-09-23", "claude-haiku-4-6")]


def test_night_upsert(tmp_path: Path) -> None:
    conn = connect(tmp_path / "runs.sqlite")
    upsert_night(conn, "2026-09-21", "running", "", 10, 0, "2026-09-21T02:00:00Z", None)
    upsert_night(conn, "2026-09-21", "complete", "", 10, 10, "2026-09-21T02:00:00Z", "2026-09-21T05:00:00Z")
    assert [tuple(r) for r in conn.execute("select status, runs_done from nights")] == [("complete", 10)]

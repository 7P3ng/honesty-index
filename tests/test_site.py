"""Generator output is checked structurally: offline banner, badge states, n gating, no scripts."""
import json
from datetime import UTC, datetime
from pathlib import Path

from harness import db
from harness.config import load_site
from harness.models import CheckResult, Claim, RunRow, RunStatus
from website.generate_site import generate

HAIKU = "claude-haiku-4-5-20251001"
TASK = "pagination-off-by-one"


def _seed(conn, night: str, n_ok: int, n_silent: int) -> None:
    for i in range(n_ok + n_silent):
        check = CheckResult.PASS if i < n_ok else CheckResult.FAIL
        db.insert_run(conn, RunRow(f"{night}-{i}", night, HAIKU, HAIKU, TASK, "test-fix", 1, RunStatus.COMPLETED, check,
                                   Claim.SUCCESS, "Done.", 0, 60000, 10, 10, 2, None,
                                   night + "T02:00:00Z", night + "T02:01:00Z"))
    db.upsert_night(conn, night, "complete", "", n_ok + n_silent, n_ok + n_silent, night + "T02:00:00Z", night + "T05:00:00Z")


def _generate(tmp_path: Path, repo_root: Path, now: datetime) -> Path:
    out = tmp_path / "build"
    generate(tmp_path / "r.sqlite", load_site(repo_root / "config" / "site.yaml"), out, now=now)
    return out


def test_offline_banner_and_badge(tmp_path: Path, repo_root: Path) -> None:
    conn = db.connect(tmp_path / "r.sqlite")
    _seed(conn, "2026-09-21", 25, 10)
    out = _generate(tmp_path, repo_root, datetime(2026, 9, 25, tzinfo=UTC))
    assert "Instrument offline since 2026-09-21" in (out / "index.html").read_text()
    assert "offline" in (out / "badge" / f"{HAIKU}.svg").read_text()
    assert json.loads((out / "status.json").read_text())["online"] is False


def test_numbers_gated_then_shown(tmp_path: Path, repo_root: Path) -> None:
    conn = db.connect(tmp_path / "r.sqlite")
    _seed(conn, "2026-09-21", 20, 9)  # 29 claimed successes → hidden
    out = _generate(tmp_path, repo_root, datetime(2026, 9, 21, 8, tzinfo=UTC))
    assert "n&lt;30 (29)" in (out / "models" / HAIKU / "index.html").read_text()
    assert "n&lt;30" in (out / "badge" / f"{HAIKU}.svg").read_text()
    _seed(conn, "2026-09-22", 20, 10)  # 7-night window: 59 claimed successes, 19 silent → shown
    out = _generate(tmp_path, repo_root, datetime(2026, 9, 22, 8, tzinfo=UTC))
    html = (out / "models" / HAIKU / "index.html").read_text()
    assert "32.2%" in html
    assert "<script" not in html
    assert "prefers-reduced-motion" in (out / "style.css").read_text()
    assert "32% (n=59)" in (out / "badge" / f"{HAIKU}.svg").read_text()


def test_status_json_csv_and_task_page(tmp_path: Path, repo_root: Path) -> None:
    conn = db.connect(tmp_path / "r.sqlite")
    _seed(conn, "2026-09-21", 3, 1)
    out = _generate(tmp_path, repo_root, datetime(2026, 9, 21, 8, tzinfo=UTC))
    status = json.loads((out / "status.json").read_text())
    assert status["last_complete_night"] == "2026-09-21" and status["online"] is True
    assert (out / "data" / "runs.csv").read_text().count("\n") == 5  # header + 4 rows
    task_html = (out / "tasks" / TASK / "index.html").read_text()
    assert "A silent failure, verbatim" in task_html and "Done." in task_html
    assert "Haiku 4.5 grades messages that Haiku 4.5 also wrote" in (out / "methodology" / "index.html").read_text()


def test_empty_database_still_renders(tmp_path: Path, repo_root: Path) -> None:
    db.connect(tmp_path / "r.sqlite")
    out = _generate(tmp_path, repo_root, datetime(2026, 9, 21, 8, tzinfo=UTC))
    assert "No runs recorded yet" in (out / "index.html").read_text()
    assert "Instrument offline since launch" in (out / "index.html").read_text()

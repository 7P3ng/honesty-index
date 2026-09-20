"""Export is exact and the archive holds every transcript; the real push is exercised once
the data repo exists (needs_github)."""
import json
import tarfile
from pathlib import Path

import subprocess

from harness import db
from harness.config import SiteConfig
from harness.models import CheckResult, Claim, RunRow, RunStatus
from harness.publish import archive_transcripts, export_night_jsonl, push_night


def test_push_night_commits_and_pushes_to_a_local_bare_repo(tmp_path: Path) -> None:
    """The git half of push_night, against a throwaway bare repo. The gh release half is
    exercised on the real data repo by the first real night (the cron wrapper alerts if it fails)."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=True)
    (clone / "README.md").write_text("x")
    subprocess.run(["git", "-C", str(clone), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(clone), "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init"], check=True)
    subprocess.run(["git", "-C", str(clone), "push", "-q", "-u", "origin", "main"], check=True)
    jsonl = tmp_path / "n.jsonl"
    jsonl.write_text('{"run_id": "a"}\n')
    cfg = SiteConfig("h", "url", clone, (1,), 30, 30)
    push_night(cfg, "2026-09-21", jsonl, None)
    log = subprocess.run(["git", "-C", str(bare), "log", "--oneline", "main"], capture_output=True, text=True, check=True).stdout
    assert log.startswith(log.split()[0]) and "night 2026-09-21" in log
    assert (clone / "nightly" / "2026-09-21.jsonl").read_text() == '{"run_id": "a"}\n'


def test_export_rows_are_complete(tmp_path: Path) -> None:
    conn = db.connect(tmp_path / "r.sqlite")
    row = RunRow("a1", "2026-09-21", "m", "m", "t", "c", 1, RunStatus.COMPLETED, CheckResult.FAIL, Claim.SUCCESS,
                 "Done.", 0, 1000, 1, 2, 3, "2026-09-21/a1.jsonl.zst", "s", "f")
    db.insert_run(conn, row, transcript_withheld=True, withheld_pattern="github_token")
    n = export_night_jsonl(conn, "2026-09-21", tmp_path / "n.jsonl")
    assert n == 1
    rec = json.loads((tmp_path / "n.jsonl").read_text().strip())
    assert rec["run_id"] == "a1" and rec["claim"] == "claimed_success" and rec["transcript_withheld"] is True
    assert rec["withheld_pattern"] == "github_token"


def test_archive_contains_every_transcript(tmp_path: Path) -> None:
    root = tmp_path / "transcripts" / "2026-09-21"
    root.mkdir(parents=True)
    (root / "a.jsonl.zst").write_bytes(b"x")
    (root / "b.jsonl.zst").write_bytes(b"y")
    n = archive_transcripts(tmp_path / "transcripts", "2026-09-21", tmp_path / "t.tar")
    assert n == 2
    with tarfile.open(tmp_path / "t.tar") as tar:
        assert sorted(tar.getnames()) == ["2026-09-21/a.jsonl.zst", "2026-09-21/b.jsonl.zst"]

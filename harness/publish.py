"""Publish a night to the public data repo (spec §7.3): rows as JSONL committed to git,
transcripts as one tar attached to a GitHub release. Fails loudly on any git/gh error;
never scrubs. The redaction decision was already made per run (runs.transcript_withheld).
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import tarfile
from pathlib import Path

from harness.config import SiteConfig


def export_night_jsonl(conn: sqlite3.Connection, night: str, dest: Path) -> int:
    """Write every run row for the night as one JSON object per line. Returns the row count."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute("select * from runs where night=? order by run_id", (night,)).fetchall()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w") as fh:
        for r in rows:
            rec = dict(r)
            rec["transcript_withheld"] = bool(rec["transcript_withheld"])
            fh.write(json.dumps(rec) + "\n")
    return len(rows)


def archive_transcripts(transcripts_root: Path, night: str, dest_tar: Path) -> int:
    """Tar every <night>/*.jsonl.zst into dest_tar. Returns the file count (0 writes an empty tar)."""
    night_dir = transcripts_root / night
    files = sorted(night_dir.glob("*.jsonl.zst")) if night_dir.exists() else []
    dest_tar.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest_tar, "w") as tar:
        for f in files:
            tar.add(f, arcname=f"{night}/{f.name}")
    return len(files)


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed in {cwd} (exit {proc.returncode}): {proc.stderr.strip()[:500]}")


def push_night(cfg: SiteConfig, night: str, jsonl: Path, tar: Path | None) -> None:
    """Side effects: commits and pushes to the data repo; creates a GitHub release with the tar.
    Raises RuntimeError naming the failing command."""
    repo = cfg.data_repo_path
    if not (repo / ".git").is_dir():
        raise RuntimeError(f"data repo checkout missing at {repo}; clone {cfg.data_repo_url} there first")
    target = repo / "nightly" / f"{night}.jsonl"
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(jsonl.read_bytes())
    _run(["git", "add", str(target.relative_to(repo))], repo)
    _run(["git", "-c", "user.name=honesty-index", "-c", "user.email=honesty-index@thomaspeng.ca",
          "commit", "-q", "--allow-empty", "-m", f"night {night}"], repo)
    _run(["git", "push", "-q"], repo)
    if tar is not None:
        _run(["gh", "release", "create", f"night-{night}", str(tar), "--title", f"Transcripts {night}",
              "--notes", f"Compressed transcripts for night {night}. Rows: nightly/{night}.jsonl"], repo)


def publish_night(conn: sqlite3.Connection, cfg: SiteConfig, night: str, transcripts_root: Path, nightly_dir: Path) -> None:
    """Export, archive, push. Local files under nightly_dir stay so a failed push can be retried."""
    jsonl = nightly_dir / f"{night}.jsonl"
    tar = nightly_dir / f"{night}-transcripts.tar"
    n_rows = export_night_jsonl(conn, night, jsonl)
    n_files = archive_transcripts(transcripts_root, night, tar)
    push_night(cfg, night, jsonl, tar if n_files else None)
    print(f"published {night}: {n_rows} rows, {n_files} transcripts", flush=True)

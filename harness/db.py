"""SQLite persistence for runs, grades, and nights (data/runs.sqlite).

grades is append-only so a re-grade under a new rubric keeps the old verdict; runs.claim
is the current verdict. Nothing here computes statistics.
"""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, fields
from datetime import UTC, datetime
from pathlib import Path

from harness.claim_grader import Grade
from harness.models import CheckResult, Claim, RunRow, RunStatus

SCHEMA_VERSION = 1
_RUN_COLUMNS = [f.name for f in fields(RunRow)]
_EXTRA_COLUMNS = ["transcript_withheld", "withheld_pattern"]

_SCHEMA = """
create table if not exists meta (key text primary key, value text not null);
create table if not exists runs (
  run_id text primary key, night text not null, model_requested text not null, model_served text,
  task text not null, category text not null, repeat integer not null, status text not null,
  check_result text not null, claim text, final_message text, exit_code integer, wall_ms integer not null,
  input_tokens integer not null, output_tokens integer not null, tool_calls integer not null,
  transcript_path text, started_at text not null, finished_at text not null,
  transcript_withheld integer not null default 0, withheld_pattern text
);
create index if not exists runs_night on runs(night);
create table if not exists grades (
  id integer primary key autoincrement, run_id text not null references runs(run_id),
  grader text not null, version text not null, label text, raw text not null, graded_at text not null
);
create table if not exists nights (
  night text primary key, status text not null, reason text not null, runs_planned integer not null,
  runs_done integer not null, started_at text not null, finished_at text
);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open (creating if needed) the database. Side effect: creates file and schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=wal")
    conn.execute("pragma foreign_keys=on")
    conn.executescript(_SCHEMA)
    conn.execute("insert or ignore into meta(key, value) values ('schema_version', ?)", (str(SCHEMA_VERSION),))
    return conn


def _plain(value: object) -> object:
    return value.value if hasattr(value, "value") else value


def insert_run(conn: sqlite3.Connection, row: RunRow, *, transcript_withheld: bool = False,
               withheld_pattern: str | None = None) -> None:
    """Insert one run. Raises sqlite3.IntegrityError on a duplicate run_id."""
    values = asdict(row)
    values["transcript_withheld"] = int(transcript_withheld)
    values["withheld_pattern"] = withheld_pattern
    cols = _RUN_COLUMNS + _EXTRA_COLUMNS
    conn.execute(
        f"insert into runs({','.join(cols)}) values ({','.join('?' for _ in cols)})",
        [_plain(values[c]) for c in cols],
    )


def insert_grade(conn: sqlite3.Connection, run_id: str, grade: Grade) -> None:
    conn.execute(
        "insert into grades(run_id, grader, version, label, raw, graded_at) values (?,?,?,?,?,?)",
        (run_id, grade.grader, grade.version, grade.label.value if grade.label else None, grade.raw,
         datetime.now(UTC).isoformat(timespec="seconds")),
    )


def set_claim(conn: sqlite3.Connection, run_id: str, claim: Claim) -> None:
    conn.execute("update runs set claim=? where run_id=?", (claim.value, run_id))


def upsert_night(conn: sqlite3.Connection, night: str, status: str, reason: str, runs_planned: int,
                 runs_done: int, started_at: str, finished_at: str | None) -> None:
    conn.execute(
        """insert into nights(night,status,reason,runs_planned,runs_done,started_at,finished_at)
           values (?,?,?,?,?,?,?)
           on conflict(night) do update set status=excluded.status, reason=excluded.reason,
           runs_planned=excluded.runs_planned, runs_done=excluded.runs_done, finished_at=excluded.finished_at""",
        (night, status, reason, runs_planned, runs_done, started_at, finished_at),
    )


def _to_row(rec: sqlite3.Row) -> RunRow:
    d = {c: rec[c] for c in _RUN_COLUMNS}
    d["status"] = RunStatus(d["status"])
    d["check_result"] = CheckResult(d["check_result"])
    d["claim"] = Claim(d["claim"]) if d["claim"] else None
    return RunRow(**d)


def _select(conn: sqlite3.Connection, where: str, params: tuple) -> list[RunRow]:
    return [_to_row(r) for r in conn.execute(f"select * from runs where {where} order by night, run_id", params)]


def runs_needing_regrade(conn: sqlite3.Connection) -> list[RunRow]:
    return _select(conn, "claim = ?", (Claim.GRADER_ERROR.value,))


def runs_between(conn: sqlite3.Connection, first_night: str, last_night: str) -> list[RunRow]:
    return _select(conn, "night between ? and ?", (first_night, last_night))


def all_runs(conn: sqlite3.Connection) -> list[RunRow]:
    return _select(conn, "1=1", ())


def nights(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("select * from nights order by night")]


def model_served_changes(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """First night of each distinct model_served per model_requested, in night order."""
    rows = conn.execute(
        """select model_requested, night, model_served from runs where model_served is not null
           group by model_requested, night, model_served order by model_requested, night"""
    ).fetchall()
    out: list[tuple[str, str, str]] = []
    last: dict[str, str] = {}
    for requested, night, served in rows:
        if last.get(requested) != served:
            out.append((requested, night, served))
            last[requested] = served
    return out

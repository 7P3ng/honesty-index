"""Pure parts of the weekly intake: date rule, licence allowlist, admission move, agent reply parsing."""
from datetime import date
from pathlib import Path

import yaml

from gate.intake import admit_candidate, category_with_fewest, licence_allowed, next_monday, parse_candidate_line
from harness.tasks import load_task
from tests.test_tasks import _write_task


def test_next_monday() -> None:
    assert next_monday(date(2026, 9, 20)) == date(2026, 9, 21)  # Sunday → tomorrow
    assert next_monday(date(2026, 9, 21)) == date(2026, 9, 28)  # Monday → next week
    assert next_monday(date(2026, 9, 23)) == date(2026, 9, 28)


def test_licence_allowlist() -> None:
    assert licence_allowed({"licence": "MIT"}) and licence_allowed({"licence": "Apache-2.0"})
    assert not licence_allowed({"licence": "GPL-3.0"})
    assert not licence_allowed({})


def test_admit_candidate_moves_and_stamps(tmp_path: Path) -> None:
    candidate = _write_task(tmp_path / "candidates", "shiny")
    (candidate / "meta.yaml").write_text("category: test-fix\ntimeout_s: 300\nsource: https://github.com/x/y/issues/1\nlicence: MIT\n")
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    dest = admit_candidate(candidate, tasks_dir, date(2026, 9, 28))
    assert dest == tasks_dir / "shiny" and not candidate.exists()
    assert load_task(dest).admitted_at == date(2026, 9, 28)
    assert yaml.safe_load((dest / "meta.yaml").read_text())["licence"] == "MIT"


def test_parse_candidate_line() -> None:
    assert parse_candidate_line("blah\n\nCANDIDATE: config-change-abc\n") == ("config-change-abc", "")
    assert parse_candidate_line("NONE: nothing suitable found") == (None, "nothing suitable found")
    assert parse_candidate_line("I did things.")[0] is None


def test_category_with_fewest_prefers_gaps(tmp_path: Path) -> None:
    for slug, cat in [("a", "test-fix"), ("b", "test-fix"), ("c", "cron-script")]:
        t = _write_task(tmp_path, slug)
        (t / "meta.yaml").write_text(f"category: {cat}\ntimeout_s: 300\nadmitted_at: 2026-09-21\nsource: authored\n")
    tasks = [load_task(p) for p in sorted(tmp_path.iterdir())]
    order = category_with_fewest(tasks)
    assert order[:3] == ["config-change", "feature-small", "refactor-safe"] and order[-1] == "test-fix"

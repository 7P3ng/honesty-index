"""Every task in the bank must load, be free of forbidden content, and not leak its check —
cheap checks that run in CI. The full prove-fail gate runs on the box (test_gate.py)."""
from pathlib import Path

from gate.prove import content_hits, leak_lines, load_wordlist
from harness.tasks import load_task


def test_all_tasks_load_clean(repo_root: Path) -> None:
    words = load_wordlist(repo_root / "gate" / "wordlist.txt")
    slugs = sorted(p.name for p in (repo_root / "tasks").iterdir() if p.is_dir())
    assert slugs, "task bank is empty"
    for slug in slugs:
        task = load_task(repo_root / "tasks" / slug)
        assert content_hits(task, words) == [], slug
        assert leak_lines(task) == [], slug
        assert task.admitted_at is not None, f"{slug} has no admitted_at"

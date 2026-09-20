"""Every line of secret_shaped.txt must be caught; ordinary transcript text must not be."""
import json
from pathlib import Path

import pytest
import zstandard

from harness.redact import scan, secret_literals_from_host, store_transcript


def test_every_secret_shape_is_caught(artifacts_dir: Path) -> None:
    for line in (artifacts_dir / "secret_shaped.txt").read_text().splitlines():
        hits = scan(line)
        assert hits, f"not caught: {line[:20]}..."
        assert all(len(h.excerpt) <= 12 for h in hits)


def test_clean_text_has_no_hits() -> None:
    assert scan("I edited paginate.py and ran python3 -m unittest; 2 tests passed. Files under /work/.") == []


def test_task_paths_are_allowed() -> None:
    assert scan("reading /home/tpeng/projects/honesty-index/tasks/foo/fixture/a.py") == []


def test_extra_literals_caught() -> None:
    hits = scan("my email is someone@example.com ok", extra_literals=("someone@example.com",))
    assert hits and hits[0].pattern_name == "host_literal"


@pytest.mark.needs_claude
def test_host_literals_exist_and_are_never_printed() -> None:
    literals = secret_literals_from_host()
    assert len(literals) >= 4 and all(len(v) >= 8 for v in literals)


def test_store_transcript_roundtrip(tmp_path: Path) -> None:
    dest = store_transcript([{"type": "assistant"}], {"type": "result"}, tmp_path / "n" / "r.jsonl.zst")
    lines = zstandard.ZstdDecompressor().decompress(dest.read_bytes(), max_output_size=10_000).decode().splitlines()
    assert [json.loads(l)["type"] for l in lines] == ["assistant", "result"]

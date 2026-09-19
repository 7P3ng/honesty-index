"""Config loading: the rotation must be deterministic from the date, and caps must be enforced."""
from datetime import date
from pathlib import Path

import pytest

from harness.config import load_budget, load_rotation, load_site, tonights_rotation


def test_rotation_every_night_models_always_present(repo_root: Path) -> None:
    rotation = load_rotation(repo_root / "config" / "rotation.yaml")
    plans = tonights_rotation(rotation, date(2026, 9, 22))
    assert {p.model for p in plans} >= {"claude-sonnet-5", "claude-haiku-4-5-20251001"}


def test_rotation_opus_every_third_night(repo_root: Path) -> None:
    rotation = load_rotation(repo_root / "config" / "rotation.yaml")
    on = {p.model for p in tonights_rotation(rotation, date(2026, 9, 21))}
    off = {p.model for p in tonights_rotation(rotation, date(2026, 9, 22))}
    assert "claude-opus-5" in on and "claude-opus-5" not in off


def test_budget_rejects_missing_field(tmp_path: Path) -> None:
    bad = tmp_path / "budget.yaml"
    bad.write_text("concurrency: 4\n")
    with pytest.raises(ValueError, match="max_runs_per_night"):
        load_budget(bad)


def test_site_config_loads(repo_root: Path) -> None:
    site = load_site(repo_root / "config" / "site.yaml")
    assert site.min_n == 30 and site.windows_nights == (1, 7, 30)

"""Load and validate config/rotation.yaml, budget.yaml, site.yaml.

Pure: reads files, returns frozen dataclasses, raises ValueError naming the file and the
missing or malformed field. No defaults are invented for missing caps — a cap that is
absent is a bug, not zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModelPlan:
    model: str
    repeats: int


@dataclass(frozen=True)
class RotationEntry:
    model: str
    night_period: int
    night_offset: int
    repeats: int


@dataclass(frozen=True)
class Rotation:
    epoch: date
    grader_model: str
    entries: tuple[RotationEntry, ...]


@dataclass(frozen=True)
class Budget:
    concurrency: int
    max_runs_per_night: int
    max_runs_per_week: int
    no_new_runs_after_utc: time
    default_timeout_s: int


@dataclass(frozen=True)
class SiteConfig:
    host: str
    data_repo_url: str
    data_repo_path: Path
    windows_nights: tuple[int, ...]
    min_n: int
    offline_after_hours: int


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text())
    except OSError as exc:
        raise ValueError(f"cannot read config file {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"config file {path} must be a mapping at top level")
    return loaded


def _require(mapping: dict[str, Any], key: str, path: Path) -> Any:
    if key not in mapping:
        raise ValueError(f"config file {path} is missing required field '{key}'")
    return mapping[key]


def load_rotation(path: Path) -> Rotation:
    """Parse rotation.yaml. Raises ValueError for a missing field or an impossible schedule."""
    raw = _read_yaml(path)
    entries = tuple(
        RotationEntry(
            model=str(_require(m, "id", path)),
            night_period=int(_require(m, "night_period", path)),
            night_offset=int(_require(m, "night_offset", path)),
            repeats=int(_require(m, "repeats", path)),
        )
        for m in _require(raw, "models", path)
    )
    for e in entries:
        if e.night_period < 1 or not (0 <= e.night_offset < e.night_period) or e.repeats < 1:
            raise ValueError(f"config file {path}: invalid rotation entry for {e.model}: {e}")
    epoch = _require(raw, "epoch", path)
    if not isinstance(epoch, date):
        raise ValueError(f"config file {path}: epoch must be a YAML date, got {epoch!r}")
    return Rotation(epoch=epoch, grader_model=str(_require(raw, "grader_model", path)), entries=entries)


def load_budget(path: Path) -> Budget:
    """Parse budget.yaml. Every cap is required."""
    raw = _read_yaml(path)
    for key in ("concurrency", "max_runs_per_night", "max_runs_per_week", "no_new_runs_after_utc", "default_timeout_s"):
        _require(raw, key, path)
    hh, mm = str(raw["no_new_runs_after_utc"]).split(":")
    return Budget(
        concurrency=int(_require(raw, "concurrency", path)),
        max_runs_per_night=int(_require(raw, "max_runs_per_night", path)),
        max_runs_per_week=int(_require(raw, "max_runs_per_week", path)),
        no_new_runs_after_utc=time(int(hh), int(mm)),
        default_timeout_s=int(_require(raw, "default_timeout_s", path)),
    )


def load_site(path: Path) -> SiteConfig:
    """Parse site.yaml."""
    raw = _read_yaml(path)
    return SiteConfig(
        host=str(_require(raw, "host", path)),
        data_repo_url=str(_require(raw, "data_repo_url", path)),
        data_repo_path=Path(str(_require(raw, "data_repo_path", path))),
        windows_nights=tuple(int(w) for w in _require(raw, "windows_nights", path)),
        min_n=int(_require(raw, "min_n", path)),
        offline_after_hours=int(_require(raw, "offline_after_hours", path)),
    )


def tonights_rotation(rotation: Rotation, night: date) -> list[ModelPlan]:
    """Models that run on `night`, in config order. Deterministic from the date alone."""
    days = (night - rotation.epoch).days
    return [
        ModelPlan(model=e.model, repeats=e.repeats)
        for e in rotation.entries
        if days % e.night_period == e.night_offset
    ]

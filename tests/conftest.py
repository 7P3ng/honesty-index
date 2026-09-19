"""Shared pytest fixtures and CI-only skipping of tests that need the real box.

CI (GitHub Actions) has neither plan auth, nor bubblewrap, nor push rights to the data
repo, so tests marked needs_claude / needs_bwrap / needs_github are skipped there — and
only there. Locally they always run: a green suite that silently skipped the real checks
is worse than a red one.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_CI_SKIPS = {
    "needs_claude": "CI has no plan auth",
    "needs_bwrap": "CI has no bubblewrap",
    "needs_github": "CI cannot push to the data repo",
}


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def artifacts_dir() -> Path:
    return REPO_ROOT / "tests" / "artifacts"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("CI") != "true":
        return
    for item in items:
        for marker, reason in _CI_SKIPS.items():
            if item.get_closest_marker(marker):
                item.add_marker(pytest.mark.skip(reason=reason))

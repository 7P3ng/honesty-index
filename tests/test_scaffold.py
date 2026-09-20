"""Proves the test runner, markers, and fixtures are wired before any real test exists."""
from pathlib import Path


def test_repo_root_fixture_points_at_pyproject(repo_root: Path) -> None:
    assert (repo_root / "pyproject.toml").is_file()

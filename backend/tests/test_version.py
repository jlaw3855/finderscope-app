"""Tests for application version metadata."""

from pathlib import Path

from app.version import read_version

REPO_VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"


def test_read_version_matches_release_file() -> None:
    expected = REPO_VERSION_FILE.read_text(encoding="utf-8").strip()
    assert read_version() == expected

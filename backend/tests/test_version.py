"""Tests for application version metadata."""

from app.version import read_version


def test_read_version_matches_release_file() -> None:
    assert read_version() == "1.0.0"

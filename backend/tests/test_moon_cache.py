"""Tests for moon enrichment cache."""

from pathlib import Path

import pytest

from app.services import moon_cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(moon_cache, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(moon_cache, "_db_path", lambda: tmp_path / "moon.db")
    monkeypatch.setattr(moon_cache, "_quota_path", lambda: tmp_path / "quota.json")
    monkeypatch.setattr(moon_cache, "_svg_dir", lambda: tmp_path / "svg")


class TestMoonCache:
    def test_store_and_read(self) -> None:
        entry = moon_cache.store_cached(
            date="2025-06-20",
            theme_key="abc123",
            phase_name="Waxing Gibbous",
            illumination_pct=94.0,
            age_days=12.4,
            is_waxing=True,
            special_labels=["Blue Moon"],
            svg="<svg viewBox='0 0 100 100'></svg>",
        )
        assert entry.svg_path is not None

        cached = moon_cache.get_cached("2025-06-20", "abc123")
        assert cached is not None
        assert cached.phase_name == "Waxing Gibbous"
        assert moon_cache.read_svg("2025-06-20", "abc123") is not None

    def test_quota_tracking(self) -> None:
        state = moon_cache.update_quota_from_headers(
            {
                "X-RateLimit-Limit": "80",
                "X-RateLimit-Remaining": "79",
                "X-RateLimit-Reset": "9999999999",
            }
        )
        assert state.daily_count == 1
        assert state.remaining == 79
        assert moon_cache.quota_available() is True

    def test_quota_exhausted(self) -> None:
        moon_cache.save_quota(moon_cache.QuotaState(daily_count=80, remaining=0, limit=80))
        assert moon_cache.quota_available() is False

"""Tests for forecast response cache."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.services import forecast_cache


@pytest.fixture
def isolated_forecast_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forecast_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(forecast_cache, "DB_PATH", tmp_path / "forecast.db")


class TestForecastCache:
    def test_geocode_key_is_stable(self) -> None:
        key_a = forecast_cache.geocode_cache_key("Denver, CO")
        key_b = forecast_cache.geocode_cache_key("  denver, co  ")
        assert key_a == key_b

    def test_coordinate_normalization(self) -> None:
        assert forecast_cache.normalize_coord(39.73923) == 39.7392

    def test_store_and_get_before_expiry(self, isolated_forecast_cache) -> None:
        payload = {"location": {"latitude": 39.7392, "longitude": -104.9903}}
        key = forecast_cache.geocode_cache_key("Denver, CO")
        forecast_cache.store_cached_entry(
            key,
            forecast_cache.LAYER_GEOCODE,
            payload,
            ttl_hours=1,
        )
        assert forecast_cache.get_cached_entry(key) == payload

    def test_expired_entry_is_not_returned(self, isolated_forecast_cache, monkeypatch) -> None:
        payload = {"location": {"latitude": 39.7392}}
        key = "test:expired"
        forecast_cache.store_cached_entry(
            key,
            forecast_cache.LAYER_GEOCODE,
            payload,
            ttl_hours=1,
        )

        expired = datetime.now(UTC) - timedelta(hours=1)
        with forecast_cache._connect() as conn:
            conn.execute(
                "UPDATE forecast_entries SET expires_at = ? WHERE cache_key = ?",
                (expired.isoformat(), key),
            )

        assert forecast_cache.get_cached_entry(key) is None

"""Timing benchmarks for hot-path forecast and astronomy services."""

from __future__ import annotations

import json
import statistics
import time
from datetime import date, timedelta
from pathlib import Path

import pytest
from app.services.astronomy_events import search_astronomy_events
from app.services.planet_visibility import compute_planet_visibility
from app.services.scoring import build_forecast

DENVER_LAT = 39.7392
DENVER_LON = -104.9903
DENVER_TZ = "America/Denver"
BENCHMARK_ITERATIONS = 5


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def _timed_seconds(func) -> float:
    start = time.perf_counter()
    func()
    return time.perf_counter() - start


@pytest.fixture(scope="module")
def denver_forecast_inputs():
    fixtures_dir = Path(__file__).parent / "fixtures"

    def _load(name: str) -> dict:
        with (fixtures_dir / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    return (
        _load("location.json"),
        _load("time_series.json"),
        _load("weather.json"),
    )


@pytest.fixture(scope="module")
def denver_forecast_dates(denver_forecast_inputs) -> list[str]:
    _, time_series_data, _ = denver_forecast_inputs
    return [day["date"] for day in time_series_data["astronomy"] if day.get("date")]


def test_benchmark_build_forecast(denver_forecast_inputs, capsys) -> None:
    location_data, time_series_data, weather_data = denver_forecast_inputs
    samples = [
        _timed_seconds(
            lambda: build_forecast(location_data, time_series_data, weather_data)
        )
        for _ in range(BENCHMARK_ITERATIONS)
    ]

    p50 = statistics.median(samples)
    p95 = _percentile(samples, 95)
    print(
        f"\n[benchmark] build_forecast p50={p50:.3f}s p95={p95:.3f}s "
        f"(n={BENCHMARK_ITERATIONS}, Denver fixtures)"
    )

    assert p50 < 5.0, f"build_forecast p50 too slow: {p50:.3f}s"


def test_benchmark_search_astronomy_events(capsys) -> None:
    samples = [
        _timed_seconds(lambda: search_astronomy_events(DENVER_LAT, DENVER_LON))
        for _ in range(BENCHMARK_ITERATIONS)
    ]

    p50 = statistics.median(samples)
    p95 = _percentile(samples, 95)
    print(
        f"\n[benchmark] search_astronomy_events p50={p50:.3f}s p95={p95:.3f}s "
        f"(n={BENCHMARK_ITERATIONS}, Denver)"
    )

    assert p50 < 10.0, f"search_astronomy_events p50 too slow: {p50:.3f}s"


def test_benchmark_compute_planet_visibility(denver_forecast_dates, capsys) -> None:
    samples = [
        _timed_seconds(
            lambda: compute_planet_visibility(
                DENVER_LAT,
                DENVER_LON,
                DENVER_TZ,
                denver_forecast_dates,
            )
        )
        for _ in range(BENCHMARK_ITERATIONS)
    ]

    p50 = statistics.median(samples)
    p95 = _percentile(samples, 95)
    print(
        f"\n[benchmark] compute_planet_visibility p50={p50:.3f}s p95={p95:.3f}s "
        f"(n={BENCHMARK_ITERATIONS}, {len(denver_forecast_dates)} nights)"
    )

    assert p50 < 5.0, f"compute_planet_visibility p50 too slow: {p50:.3f}s"


def test_benchmark_forecast_cache_cold_vs_warm(denver_forecast_inputs, tmp_path, monkeypatch) -> None:
    """Document cache miss vs hit latency for forecast upstream layers."""
    from app.services import forecast_cache

    monkeypatch.setattr(forecast_cache, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(forecast_cache, "_db_path", lambda: tmp_path / "forecast.db")

    location_data, time_series_data, weather_data = denver_forecast_inputs
    latitude = float(location_data["location"]["latitude"])
    longitude = float(location_data["location"]["longitude"])
    date_start = date(2025, 6, 20)
    date_end = date(2025, 6, 21)

    geocode_key = forecast_cache.geocode_cache_key("Denver, CO")
    ts_key = forecast_cache.astronomy_cache_key(
        latitude,
        longitude,
        (date_start - timedelta(days=1)).isoformat(),
        date_end.isoformat(),
    )
    weather_key = forecast_cache.weather_cache_key(
        latitude,
        longitude,
        date_start.isoformat(),
        7,
    )

    cold = _timed_seconds(
        lambda: (
            forecast_cache.store_cached_entry(geocode_key, forecast_cache.LAYER_GEOCODE, location_data, ttl_hours=24),
            forecast_cache.store_cached_entry(ts_key, forecast_cache.LAYER_ASTRONOMY, time_series_data, ttl_hours=24),
            forecast_cache.store_cached_entry(weather_key, forecast_cache.LAYER_WEATHER, weather_data, ttl_hours=1),
        )
    )
    warm = _timed_seconds(
        lambda: (
            forecast_cache.get_cached_entry(geocode_key),
            forecast_cache.get_cached_entry(ts_key),
            forecast_cache.get_cached_entry(weather_key),
        )
    )

    print(
        f"\n[benchmark] forecast_cache store(cold)={cold:.4f}s read(warm)={warm:.4f}s "
        "(SQLite, 3 layers, Denver fixtures)"
    )

    assert warm <= cold or warm < 0.05

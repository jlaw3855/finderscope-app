"""Unit tests for scoring logic and forecast assembly."""

from datetime import datetime

import pytest

from app.models.forecast import HourlyScore
from app.services.scoring import (
    MoonIlluminationAnchor,
    _find_best_hours,
    _hour_score,
    _interpolate_illumination,
    _is_in_nights_darkness,
    _parse_illumination,
    _parse_time,
    _rating_from_score,
    _resolve_moon_illumination,
    _weather_penalty,
    build_forecast,
)


class TestParseTime:
    def test_parse_time(self) -> None:
        assert _parse_time("21:30") == (21, 30)


class TestRatingFromScore:
    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (85, "Excellent"),
            (80, "Excellent"),
            (65, "Good"),
            (45, "Fair"),
            (20, "Poor"),
        ],
    )
    def test_rating_thresholds(self, score: int, expected: str) -> None:
        assert _rating_from_score(score) == expected


class TestWeatherPenalty:
    def test_clear_weather(self) -> None:
        assert _weather_penalty(0) == 100.0

    def test_bad_weather_code(self) -> None:
        assert _weather_penalty(61) == 0.0

    def test_missing_weather_code(self) -> None:
        assert _weather_penalty(None) == 50.0


class TestHourScore:
    def test_ideal_conditions(self) -> None:
        score = _hour_score(
            cloud_cover=0,
            visibility=10000,
            moon_illumination=0,
            precipitation=0,
            weather_code=0,
        )
        assert score == 100

    def test_heavy_clouds_reduce_score(self) -> None:
        score = _hour_score(
            cloud_cover=100,
            visibility=10000,
            moon_illumination=0,
            precipitation=0,
            weather_code=0,
        )
        assert score == 60


class TestNightsDarkness:
    def test_evening_hour_in_window(self) -> None:
        hour_dt = datetime.fromisoformat("2025-06-20T22:00")
        assert _is_in_nights_darkness(hour_dt, "2025-06-20", "21:30", "04:45")

    def test_morning_hour_on_next_day(self) -> None:
        hour_dt = datetime.fromisoformat("2025-06-21T04:00")
        assert _is_in_nights_darkness(hour_dt, "2025-06-20", "21:30", "04:45")

    def test_excludes_previous_night_tail_on_same_day(self) -> None:
        hour_dt = datetime.fromisoformat("2025-06-20T06:00")
        assert not _is_in_nights_darkness(hour_dt, "2025-06-20", "21:30", "04:45")

    def test_excludes_morning_after_window(self) -> None:
        hour_dt = datetime.fromisoformat("2025-06-21T06:00")
        assert not _is_in_nights_darkness(hour_dt, "2025-06-20", "21:30", "04:45")


class TestFindBestHours:
    def test_contiguous_high_score_window(self) -> None:
        hourly = [
            HourlyScore(time="21:00", at="2025-06-20T21:00", score=60),
            HourlyScore(time="22:00", at="2025-06-20T22:00", score=75),
            HourlyScore(time="23:00", at="2025-06-20T23:00", score=85),
            HourlyScore(time="00:00", at="2025-06-21T00:00", score=80),
            HourlyScore(time="01:00", at="2025-06-21T01:00", score=65),
        ]
        windows = _find_best_hours(hourly, threshold=70)
        assert len(windows) == 1
        assert windows[0].start == "22:00"
        assert windows[0].end == "00:00"
        assert windows[0].score == 80


class TestMoonIllumination:
    def test_parse_negative_waning_value(self) -> None:
        assert _parse_illumination(-72.5) == 72.5

    def test_interpolate_from_anchor(self) -> None:
        anchor = MoonIlluminationAnchor(
            anchor_date=datetime.fromisoformat("2025-06-20").date(),
            illumination=72.5,
            lunar_age_days=18.5,
        )
        result = _interpolate_illumination(anchor, "2025-06-21", "LAST_QUARTER")
        assert 0 <= result <= 100

    def test_resolve_direct_illumination(self) -> None:
        day = {"moon_illumination_percentage": 45.0, "moon_phase": "FIRST_QUARTER"}
        assert _resolve_moon_illumination(day, None, "2025-06-20") == 45.0


class TestBuildForecast:
    def test_build_forecast_from_fixtures(self, load_fixture) -> None:
        location_data = load_fixture("location.json")
        time_series_data = load_fixture("time_series.json")
        weather_data = load_fixture("weather.json")

        result = build_forecast(location_data, time_series_data, weather_data)

        assert result.location.label == "Denver, Colorado, United States"
        assert result.location.latitude == pytest.approx(39.7392)
        assert len(result.nights) == 2

        first_night = result.nights[0]
        assert first_night.date == "2025-06-20"
        assert first_night.dark_window is not None
        assert first_night.dark_window.start == "21:30"
        assert first_night.moon_illumination == pytest.approx(72.5)
        assert first_night.temperature_high == pytest.approx(28)
        assert first_night.temperature_low == pytest.approx(12)
        assert len(first_night.hourly) >= 3
        assert all(entry.score >= 0 for entry in first_night.hourly)

        hour_times = {entry.time for entry in first_night.hourly}
        assert "06:00" not in hour_times
        assert "23:00" in hour_times

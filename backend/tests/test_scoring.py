"""Unit tests for scoring logic and forecast assembly."""

from datetime import datetime
from unittest.mock import patch

import pytest

from app.models.forecast import HourlyScore
from app.services.scoring import (
    MoonIlluminationAnchor,
    _darkness_slots_for_night,
    _effective_moon_illumination,
    _find_best_hours,
    _half_hour_slots_from_hourly_times,
    _hour_score,
    _interpolate_illumination,
    _is_moon_up,
    _is_moon_up_at_minutes,
    _is_in_nights_darkness,
    _parse_illumination,
    _parse_time,
    _rating_from_score,
    _resolve_moon_illumination,
    _resolve_night_moon_times,
    _weather_penalty,
    build_forecast,
)

DENVER_LAT = 39.7392
DENVER_LON = -104.9903
DENVER_TZ = "America/Denver"


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

    def test_darkness_slot_narrowing_matches_global_scan(self, load_fixture) -> None:
        weather_data = load_fixture("weather.json")
        time_series_data = load_fixture("time_series.json")
        hourly_times = weather_data.get("hourly", {}).get("time", [])
        score_slots = _half_hour_slots_from_hourly_times(hourly_times)

        for day in time_series_data["astronomy"]:
            day_date = day.get("date", "")
            night_begin = day.get("night_begin")
            night_end = day.get("night_end") or day.get("morning", {}).get(
                "astronomical_twilight_end"
            )
            if not night_begin or not night_end:
                continue

            filtered = [
                slot_dt
                for slot_dt in score_slots
                if _is_in_nights_darkness(slot_dt, day_date, night_begin, night_end)
            ]
            narrowed = _darkness_slots_for_night(day_date, night_begin, night_end, score_slots)
            assert narrowed == filtered


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


class TestMoonriseMoonset:
    def test_same_day_rise_before_set(self) -> None:
        assert _is_moon_up_at_minutes(12 * 60, 6 * 60, 18 * 60) is True
        assert _is_moon_up_at_minutes(5 * 60, 6 * 60, 18 * 60) is False

    def test_overnight_moon_window(self) -> None:
        assert _is_moon_up_at_minutes(23 * 60, 22 * 60, 4 * 60) is True
        assert _is_moon_up_at_minutes(3 * 60, 22 * 60, 4 * 60) is True
        assert _is_moon_up_at_minutes(21 * 60, 22 * 60, 4 * 60) is False

    def test_moon_up_before_rise(self) -> None:
        astronomy = {
            "2025-06-20": {"date": "2025-06-20", "moonrise": "23:00", "moonset": "-:-"},
            "2025-06-21": {"date": "2025-06-21", "moonrise": "-:-", "moonset": "04:00"},
        }
        hour_before_rise = datetime.fromisoformat("2025-06-20T22:00")
        hour_after_rise = datetime.fromisoformat("2025-06-20T23:00")
        hour_before_set = datetime.fromisoformat("2025-06-21T03:00")

        assert _is_moon_up(hour_before_rise, astronomy) is False
        assert _is_moon_up(hour_after_rise, astronomy) is True
        assert _is_moon_up(hour_before_set, astronomy) is True

    def test_effective_illumination_zero_when_moon_down(self) -> None:
        astronomy = {
            "2025-06-20": {"date": "2025-06-20", "moonrise": "23:00", "moonset": "-:-"},
        }
        hour_dt = datetime.fromisoformat("2025-06-20T22:00")
        effective, moon_up, altitude = _effective_moon_illumination(
            hour_dt,
            72.5,
            astronomy,
            DENVER_LAT,
            DENVER_LON,
            DENVER_TZ,
        )
        assert effective == 0.0
        assert moon_up is False
        assert altitude is not None
        assert altitude <= 0

    def test_effective_illumination_scales_with_altitude(self) -> None:
        astronomy = {
            "2025-06-20": {"date": "2025-06-20", "moonrise": "23:00", "moonset": "-:-"},
            "2025-06-21": {"date": "2025-06-21", "moonrise": "-:-", "moonset": "04:00"},
        }
        hour_low = datetime.fromisoformat("2025-06-21T02:00")
        hour_higher = datetime.fromisoformat("2025-06-21T04:00")
        low_effective, low_up, _ = _effective_moon_illumination(
            hour_low,
            72.5,
            astronomy,
            DENVER_LAT,
            DENVER_LON,
            DENVER_TZ,
        )
        high_effective, high_up, _ = _effective_moon_illumination(
            hour_higher,
            72.5,
            astronomy,
            DENVER_LAT,
            DENVER_LON,
            DENVER_TZ,
        )
        assert low_up is True
        assert high_up is True
        assert 0 < low_effective < high_effective < 72.5

    def test_effective_illumination_falls_back_when_altitude_unavailable(self) -> None:
        astronomy = {
            "2025-06-20": {"date": "2025-06-20", "moonrise": "22:00", "moonset": "04:00"},
        }
        hour_dt = datetime.fromisoformat("2025-06-20T23:00")
        with patch(
            "app.services.scoring.moon_position.moon_altitude_deg",
            side_effect=RuntimeError("moon altitude unavailable"),
        ):
            effective, moon_up, altitude = _effective_moon_illumination(
                hour_dt,
                72.5,
                astronomy,
                DENVER_LAT,
                DENVER_LON,
                DENVER_TZ,
            )
        assert effective == pytest.approx(72.5)
        assert moon_up is True
        assert altitude is None

    def test_moon_down_hours_score_higher(self) -> None:
        base_kwargs = {
            "cloud_cover": 0,
            "visibility": 10000,
            "precipitation": 0,
            "weather_code": 0,
        }
        score_moon_up = _hour_score(moon_illumination=80.0, **base_kwargs)
        score_moon_down = _hour_score(moon_illumination=0.0, **base_kwargs)
        assert score_moon_down > score_moon_up

    def test_resolve_night_moon_times(self) -> None:
        astronomy = {
            "2025-06-20": {"date": "2025-06-20", "moonrise": "23:00", "moonset": "-:-"},
            "2025-06-21": {"date": "2025-06-21", "moonrise": "-:-", "moonset": "04:00"},
        }
        moonrise, moonset = _resolve_night_moon_times(astronomy["2025-06-20"], astronomy)
        assert moonrise == "23:00"
        assert moonset == "04:00"


class TestBuildForecast:
    def test_build_forecast_from_fixtures(self, load_fixture) -> None:
        location_data = load_fixture("location.json")
        time_series_data = load_fixture("time_series.json")
        weather_data = load_fixture("weather.json")

        result = build_forecast(location_data, time_series_data, weather_data)

        assert result.score_step_minutes == 30
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
        assert "21:30" in hour_times
        assert "23:00" in hour_times
        assert "22:30" in hour_times

        hour_22 = next(entry for entry in first_night.hourly if entry.time == "22:00")
        hour_04 = next(entry for entry in first_night.hourly if entry.time == "04:00")
        assert hour_22.moon_up is False
        assert hour_22.moon_illumination_effective == 0.0
        assert hour_04.moon_up is True
        assert 0 < hour_04.moon_illumination_effective < first_night.moon_illumination
        assert first_night.moon_sky_glow_avg is not None
        assert first_night.moon_sky_glow_avg < first_night.moon_illumination
        expected_avg = round(
            sum(entry.moon_illumination_effective or 0 for entry in first_night.hourly)
            / len(first_night.hourly),
            1,
        )
        assert first_night.moon_sky_glow_avg == pytest.approx(expected_avg)
        assert first_night.moonrise == "23:00"
        assert first_night.moonset == "04:00"

    def test_last_night_includes_post_midnight_hours(self, load_fixture) -> None:
        """The final night's darkness spans into the next calendar day."""
        location_data = load_fixture("location.json")
        time_series_data = {
            "astronomy": [
                {
                    "date": "2025-07-02",
                    "moon_phase": "WANING_GIBBOUS",
                    "night_begin": "21:30",
                    "night_end": "04:45",
                }
            ]
        }
        weather_data = {
            "timezone": "America/Los_Angeles",
            "hourly": {
                "time": [
                    "2025-07-02T22:00",
                    "2025-07-02T23:00",
                    "2025-07-03T00:00",
                    "2025-07-03T01:00",
                    "2025-07-03T02:00",
                    "2025-07-03T03:00",
                    "2025-07-03T04:00",
                ],
                "cloud_cover": [5, 5, 5, 5, 5, 5, 5],
                "cloud_cover_low": [1, 1, 1, 1, 1, 1, 1],
                "cloud_cover_mid": [1, 1, 1, 1, 1, 1, 1],
                "cloud_cover_high": [1, 1, 1, 1, 1, 1, 1],
                "visibility": [20000] * 7,
                "precipitation": [0] * 7,
                "precipitation_probability": [0] * 7,
                "weather_code": [0] * 7,
                "dew_point_2m": [50] * 7,
                "temperature_2m": [60] * 7,
            },
            "daily": {
                "time": ["2025-07-02"],
                "temperature_2m_max": [80],
                "temperature_2m_min": [55],
                "precipitation_sum": [0.0],
            },
        }

        result = build_forecast(location_data, time_series_data, weather_data)

        assert result.score_step_minutes == 30
        last_night = result.nights[0]
        assert last_night.date == "2025-07-02"
        hour_times = {entry.time for entry in last_night.hourly}
        assert hour_times == {
            "22:00",
            "22:30",
            "23:00",
            "23:30",
            "00:00",
            "00:30",
            "01:00",
            "01:30",
            "02:00",
            "02:30",
            "03:00",
            "03:30",
            "04:00",
        }
        assert all(entry.at.startswith("2025-07-03") for entry in last_night.hourly[4:])

    def test_half_hour_slots_interpolate_from_hourly_when_minutely_missing(self, load_fixture) -> None:
        location_data = load_fixture("location.json")
        time_series_data = {
            "astronomy": [
                {
                    "date": "2025-07-02",
                    "moon_phase": "WANING_GIBBOUS",
                    "night_begin": "22:00",
                    "night_end": "23:00",
                }
            ]
        }
        weather_data = {
            "timezone": "America/Denver",
            "hourly": {
                "time": ["2025-07-02T22:00", "2025-07-02T23:00"],
                "cloud_cover": [10, 30],
                "cloud_cover_low": [1, 3],
                "cloud_cover_mid": [2, 4],
                "cloud_cover_high": [3, 5],
                "visibility": [20000, 15000],
                "precipitation": [0, 0.2],
                "precipitation_probability": [0, 20],
                "weather_code": [0, 61],
                "dew_point_2m": [50, 52],
                "temperature_2m": [60, 58],
            },
            "daily": {
                "time": ["2025-07-02"],
                "temperature_2m_max": [80],
                "temperature_2m_min": [55],
                "precipitation_sum": [0.2],
            },
        }

        result = build_forecast(location_data, time_series_data, weather_data)
        night = result.nights[0]
        half_hour = next(entry for entry in night.hourly if entry.time == "22:30")

        assert half_hour.cloud_cover == pytest.approx(20)
        assert half_hour.precipitation == pytest.approx(0.0)

    def test_prior_day_dark_window_from_extended_time_series(self, load_fixture) -> None:
        from datetime import date

        location_data = load_fixture("location.json")
        weather_data = load_fixture("weather.json")
        base_day = load_fixture("time_series.json")["astronomy"][0]
        prior_day = {**base_day, "date": "2025-06-19"}
        time_series_data = {
            "astronomy": [prior_day, *load_fixture("time_series.json")["astronomy"]],
        }

        result = build_forecast(
            location_data,
            time_series_data,
            weather_data,
            forecast_start=date(2025, 6, 20),
            forecast_end=date(2025, 6, 21),
        )

        assert len(result.nights) == 2
        assert result.prior_day_dark_window is not None
        assert result.prior_day_dark_window.start == "21:30"
        assert result.prior_day_dark_window.end == "04:45"

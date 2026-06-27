"""Tests for meteor shower peak highlights on forecast nights."""

from datetime import date

from app.services.meteor_showers import (
    is_radiant_visible_during_dark_window,
    meteor_highlights_for_night,
    showers_peaking_on,
)
from app.services.scoring import build_forecast


class TestMeteorShowerCatalog:
    def test_showers_peaking_on_perseids_date(self) -> None:
        showers = showers_peaking_on(date(2026, 8, 12))
        names = [shower["name"] for shower in showers]
        assert "Perseids" in names

    def test_showers_peaking_on_non_peak_date_empty(self) -> None:
        assert showers_peaking_on(date(2026, 6, 20)) == []


class TestRadiantVisibility:
    def test_perseids_visible_during_denver_dark_window(self) -> None:
        assert is_radiant_visible_during_dark_window(
            39.7392,
            -104.9903,
            "America/Denver",
            "2026-08-12",
            "21:30",
            "04:45",
            3.07,
            58.0,
        )

    def test_perseids_not_visible_from_southern_hemisphere_on_peak(self) -> None:
        assert not is_radiant_visible_during_dark_window(
            -37.8136,
            144.9631,
            "Australia/Melbourne",
            "2026-08-12",
            "21:30",
            "04:45",
            3.07,
            58.0,
        )


class TestMeteorHighlightsForNight:
    def test_returns_perseids_for_peak_night(self) -> None:
        highlights = meteor_highlights_for_night(
            39.7392,
            -104.9903,
            "America/Denver",
            "2026-08-12",
            "21:30",
            "04:45",
        )
        assert len(highlights) == 1
        assert highlights[0].id == "PER"
        assert highlights[0].name == "Perseids"
        assert highlights[0].zhr_nominal == 100

    def test_returns_empty_without_dark_window_times(self) -> None:
        assert meteor_highlights_for_night(
            39.7392,
            -104.9903,
            "America/Denver",
            "2026-08-12",
            "",
            "",
        ) == []


class TestBuildForecastMeteorHighlights:
    def test_attaches_meteor_showers_on_peak_night(self, load_fixture) -> None:
        location_data = load_fixture("location.json")
        weather_data = load_fixture("weather.json")
        base_day = load_fixture("time_series.json")["astronomy"][0]
        peak_day = {**base_day, "date": "2026-08-12"}
        time_series_data = {"astronomy": [peak_day]}

        result = build_forecast(
            location_data,
            time_series_data,
            weather_data,
            forecast_start=date(2026, 8, 12),
            forecast_end=date(2026, 8, 12),
        )

        assert len(result.nights) == 1
        assert len(result.nights[0].meteor_showers) == 1
        assert result.nights[0].meteor_showers[0].name == "Perseids"

    def test_no_meteor_showers_on_non_peak_night(self, load_fixture) -> None:
        location_data = load_fixture("location.json")
        weather_data = load_fixture("weather.json")
        base_day = load_fixture("time_series.json")["astronomy"][0]
        regular_day = {**base_day, "date": "2026-06-20"}
        time_series_data = {"astronomy": [regular_day]}

        result = build_forecast(
            location_data,
            time_series_data,
            weather_data,
            forecast_start=date(2026, 6, 20),
            forecast_end=date(2026, 6, 20),
        )

        assert result.nights[0].meteor_showers == []

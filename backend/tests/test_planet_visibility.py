"""Tests for planet visibility calculations."""

from app.services.planet_visibility import compute_planet_visibility


class TestPlanetVisibility:
    def test_jupiter_visible_with_twilight_windows_in_denver(self) -> None:
        results = compute_planet_visibility(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2026-06-27"],
        )
        assert len(results) == 1
        jupiter = next(row for row in results[0].planets if row.body == "Jupiter")
        assert jupiter.visible is True
        assert len(jupiter.windows_civil) >= 1
        assert jupiter.peak_at is not None
        assert jupiter.peak_altitude_deg is not None
        assert jupiter.peak_altitude_deg > 0
        assert jupiter.magnitude is not None

    def test_excludes_daytime_above_horizon_windows(self) -> None:
        results = compute_planet_visibility(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2025-06-20"],
        )
        mars = next(row for row in results[0].planets if row.body == "Mars")
        assert mars.visible is True
        assert mars.peak_at is not None
        peak_hour = int(mars.peak_at.split(":")[0])
        assert peak_hour >= 21 or peak_hour <= 5
        for window in mars.windows_civil:
            start_hour = int(window.start.split(":")[0])
            end_hour = int(window.end.split(":")[0])
            assert start_hour >= 21 or start_hour <= 5
            assert end_hour >= 21 or end_hour <= 5 or window.end in {"23:59", "24:00"}

    def test_astronomical_windows_are_subset_of_civil(self) -> None:
        results = compute_planet_visibility(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2025-06-20"],
        )
        for day in results:
            for planet in day.planets:
                if not planet.visible:
                    continue
                assert len(planet.windows_astronomical) <= len(planet.windows_civil)

    def test_returns_row_for_each_forecast_date(self) -> None:
        dates = ["2026-06-27", "2026-06-28", "2026-06-29"]
        results = compute_planet_visibility(39.7392, -104.9903, "America/Denver", dates)
        assert [day.date for day in results] == dates
        for day in results:
            assert len(day.planets) >= 5

"""Tests for planet visibility calculations."""

from app.services.planet_visibility import compute_planet_visibility


class TestPlanetVisibility:
    def test_jupiter_visible_with_windows_in_denver(self) -> None:
        results = compute_planet_visibility(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2026-06-27"],
        )
        assert len(results) == 1
        jupiter = next(row for row in results[0].planets if row.body == "Jupiter")
        assert jupiter.visible is True
        assert len(jupiter.windows) >= 1
        assert jupiter.windows[0].start
        assert jupiter.windows[0].end
        assert jupiter.peak_at is not None
        assert jupiter.peak_altitude_deg is not None
        assert jupiter.peak_altitude_deg > 0
        assert jupiter.magnitude is not None

    def test_returns_row_for_each_forecast_date(self) -> None:
        dates = ["2026-06-27", "2026-06-28", "2026-06-29"]
        results = compute_planet_visibility(39.7392, -104.9903, "America/Denver", dates)
        assert [day.date for day in results] == dates
        for day in results:
            assert len(day.planets) >= 5

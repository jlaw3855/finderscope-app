"""Tests for rise, set, and transit almanac calculations."""

from app.services.celestial_almanac import compute_celestial_almanac


class TestCelestialAlmanac:
    def test_returns_rows_for_each_forecast_date(self) -> None:
        dates = ["2026-06-27", "2026-06-28"]
        results = compute_celestial_almanac(39.7392, -104.9903, "America/Denver", dates)
        assert [day.date for day in results] == dates
        for day in results:
            bodies = [row.body for row in day.rows]
            assert bodies[:3] == ["Sun", "Moon", "Mercury"]
            assert "Jupiter" in bodies
            assert "Neptune" in bodies

    def test_jupiter_has_rise_transit_set_on_denver_night(self) -> None:
        results = compute_celestial_almanac(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2026-06-27"],
        )
        jupiter = next(row for row in results[0].rows if row.body == "Jupiter")
        assert jupiter.always_up is False
        assert jupiter.always_down is False
        assert jupiter.rise_at is not None
        assert jupiter.transit_at is not None
        assert jupiter.set_at is not None
        assert jupiter.transit_altitude_deg is not None
        assert jupiter.transit_altitude_deg > 0

        rise_minutes = _hhmm_to_minutes(jupiter.rise_at)
        transit_minutes = _hhmm_to_minutes(jupiter.transit_at)
        set_minutes = _hhmm_to_minutes(jupiter.set_at)
        assert rise_minutes < transit_minutes < set_minutes

    def test_sun_transit_near_midday(self) -> None:
        results = compute_celestial_almanac(
            39.7392,
            -104.9903,
            "America/Denver",
            ["2026-06-27"],
        )
        sun = next(row for row in results[0].rows if row.body == "Sun")
        assert sun.transit_at is not None
        transit_hour = int(sun.transit_at.split(":")[0])
        assert 11 <= transit_hour <= 14
        assert sun.transit_altitude_deg is not None
        assert sun.transit_altitude_deg > 60


def _hhmm_to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)

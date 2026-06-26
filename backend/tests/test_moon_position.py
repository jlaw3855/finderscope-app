"""Unit tests for Skyfield moon altitude and sky-glow curve."""

from datetime import datetime

import pytest

from app.services.moon_position import (
    effective_moon_illumination,
    ensure_ephemeris,
    moon_altitude_deg,
    sky_brightness_factor,
)


@pytest.fixture(scope="module", autouse=True)
def _load_ephemeris() -> None:
    ensure_ephemeris()


class TestSkyBrightnessFactor:
    def test_below_horizon(self) -> None:
        assert sky_brightness_factor(-5) == 0.0
        assert sky_brightness_factor(0) == 0.0

    def test_at_zenith(self) -> None:
        assert sky_brightness_factor(90) == pytest.approx(1.0)

    def test_at_thirty_degrees(self) -> None:
        assert sky_brightness_factor(30) == pytest.approx(0.5, abs=0.01)


class TestEffectiveMoonIllumination:
    def test_zero_altitude(self) -> None:
        assert effective_moon_illumination(80, 0) == 0.0

    def test_full_altitude(self) -> None:
        assert effective_moon_illumination(80, 90) == pytest.approx(80.0)


class TestMoonAltitudeDeg:
    def test_returns_float_for_denver(self) -> None:
        altitude = moon_altitude_deg(
            39.7392,
            -104.9903,
            datetime(2025, 6, 20, 23, 30),
            "America/Denver",
        )
        assert isinstance(altitude, float)

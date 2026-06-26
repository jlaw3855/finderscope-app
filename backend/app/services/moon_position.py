"""Moon altitude and sky-glow helpers using Skyfield."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from skyfield.api import Loader, wgs84

EPHEMERIS_DIR = Path(__file__).resolve().parents[2] / "data" / "ephemeris"
EPHEMERIS_FILENAME = "de421.bsp"


def sky_brightness_factor(altitude_deg: float) -> float:
    """Map moon altitude to a 0..1 sky-glow multiplier."""
    if altitude_deg <= 0:
        return 0.0
    return math.sin(math.radians(min(altitude_deg, 90.0)))


def effective_moon_illumination(phase_pct: float, altitude_deg: float) -> float:
    """Scale phase illumination by altitude-driven sky brightness."""
    return round(phase_pct * sky_brightness_factor(altitude_deg), 1)


@lru_cache(maxsize=1)
def _loader() -> Loader:
    EPHEMERIS_DIR.mkdir(parents=True, exist_ok=True)
    return Loader(str(EPHEMERIS_DIR))


def ensure_ephemeris() -> None:
    """Download and cache the JPL ephemeris used for moon altitude."""
    load = _loader()
    load(EPHEMERIS_FILENAME)


@lru_cache(maxsize=1)
def _earth_moon():
    load = _loader()
    planets = load(EPHEMERIS_FILENAME)
    return planets["earth"], planets["moon"], load.timescale()


def moon_altitude_deg(
    latitude: float,
    longitude: float,
    dt_local: datetime,
    timezone_name: str,
) -> float:
    """Return topocentric apparent moon altitude in degrees at a local datetime."""
    tz = ZoneInfo(timezone_name)
    if dt_local.tzinfo is None:
        dt_aware = dt_local.replace(tzinfo=tz)
    else:
        dt_aware = dt_local.astimezone(tz)

    earth, moon, timescale = _earth_moon()
    t = timescale.from_datetime(dt_aware)
    observer = earth + wgs84.latlon(latitude, longitude)
    alt, _, _ = (observer.at(t).observe(moon).apparent().altaz())
    return float(alt.degrees)


def sample_interval_midpoint(interval_dt: datetime, step_minutes: int = 30) -> datetime:
    """Sample moon position at the middle of a score interval bucket."""
    return interval_dt + timedelta(minutes=step_minutes // 2)


def sample_hour_midpoint(hour_dt: datetime) -> datetime:
    """Sample moon position at the middle of an hourly bucket."""
    return sample_interval_midpoint(hour_dt, 60)

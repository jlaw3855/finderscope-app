"""Moon altitude and sky-glow helpers using astronomy-engine."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from astronomy import Body, Observer

from app.services.astronomy_geometry import altitude_deg
from app.services.astronomy_time import cached_zoneinfo, local_datetime_to_time


def sky_brightness_factor(altitude_deg: float) -> float:
    """Map moon altitude to a 0..1 sky-glow multiplier."""
    if altitude_deg <= 0:
        return 0.0
    return math.sin(math.radians(min(altitude_deg, 90.0)))


def effective_moon_illumination(phase_pct: float, altitude_deg: float) -> float:
    """Scale phase illumination by altitude-driven sky brightness."""
    return round(phase_pct * sky_brightness_factor(altitude_deg), 1)


def moon_altitude_deg(
    latitude: float,
    longitude: float,
    dt_local: datetime,
    timezone_name: str,
) -> float:
    """Return topocentric apparent moon altitude in degrees at a local datetime."""
    tz = cached_zoneinfo(timezone_name)
    if dt_local.tzinfo is None:
        dt_aware = dt_local.replace(tzinfo=tz)
    else:
        dt_aware = dt_local.astimezone(tz)

    observer = Observer(latitude, longitude, 0.0)
    moment = local_datetime_to_time(dt_aware)
    return altitude_deg(Body.Moon, observer, moment)


def sample_interval_midpoint(interval_dt: datetime, step_minutes: int = 30) -> datetime:
    """Sample moon position at the middle of a score interval bucket."""
    return interval_dt + timedelta(minutes=step_minutes // 2)


def sample_hour_midpoint(hour_dt: datetime) -> datetime:
    """Sample moon position at the middle of an hourly bucket."""
    return sample_interval_midpoint(hour_dt, 60)

"""Jupiter moon positions and Saturn ring tilt for planet visibility rows."""

from __future__ import annotations

import math
from typing import Literal

from astronomy import (
    AngleBetween,
    Body,
    Equator,
    EquatorFromVector,
    GeoVector,
    Illumination,
    JupiterMoons,
    Observer,
    Time,
    Vector,
)

from app.models.astronomy import JupiterMoonOffset, JupiterMoonsDetail
from app.services.astronomy_time import (
    cached_zoneinfo,
    calendar_day_bounds,
    parse_calendar_date,
)

JUPITER_MOON_NAMES: tuple[Literal["Io", "Europa", "Ganymede", "Callisto"], ...] = (
    "Io",
    "Europa",
    "Ganymede",
    "Callisto",
)

JUPITER_MOON_ATTRS = ("io", "europa", "ganymede", "callisto")


def _position_angle_deg(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    ra1_rad, dec1_rad, ra2_rad, dec2_rad = map(
        math.radians,
        [ra1, dec1, ra2, dec2],
    )
    y = math.sin(ra2_rad - ra1_rad)
    x = math.cos(dec1_rad) * math.tan(dec2_rad) - math.sin(dec1_rad) * math.cos(
        ra2_rad - ra1_rad
    )
    return math.degrees(math.atan2(y, x)) % 360.0


def _peak_time_from_hhmm(
    date_str: str,
    peak_at: str,
    timezone_name: str,
) -> Time | None:
    from datetime import datetime, time

    try:
        hour, minute = map(int, peak_at.split(":"))
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    day = parse_calendar_date(date_str)
    tz = cached_zoneinfo(timezone_name)
    local_dt = datetime.combine(day, time(hour, minute), tzinfo=tz)
    from app.services.astronomy_time import local_datetime_to_time

    return local_datetime_to_time(local_dt)


def compute_jupiter_moons(
    observer: Observer,
    date_str: str,
    peak_at: str,
    timezone_name: str,
) -> JupiterMoonsDetail | None:
    sample_time = _peak_time_from_hhmm(date_str, peak_at, timezone_name)
    if sample_time is None:
        return None

    day_start, day_end = calendar_day_bounds(date_str, timezone_name)
    if sample_time.ut < day_start.ut or sample_time.ut > day_end.ut:
        return None

    jupiter_geo = GeoVector(Body.Jupiter, sample_time, True)
    jupiter_eq = Equator(Body.Jupiter, sample_time, observer, True, True)
    moons_info = JupiterMoons(sample_time)
    offsets: list[JupiterMoonOffset] = []

    for label, attr in zip(JUPITER_MOON_NAMES, JUPITER_MOON_ATTRS, strict=True):
        state = getattr(moons_info, attr)
        moon_geo = Vector(
            jupiter_geo.x + state.x,
            jupiter_geo.y + state.y,
            jupiter_geo.z + state.z,
            jupiter_geo.t,
        )
        moon_eq = EquatorFromVector(moon_geo)
        separation_arcmin = AngleBetween(jupiter_geo, moon_geo) * 60.0
        position_angle = _position_angle_deg(
            jupiter_eq.ra,
            jupiter_eq.dec,
            moon_eq.ra,
            moon_eq.dec,
        )
        east_arcmin = separation_arcmin * math.sin(math.radians(position_angle))
        north_arcmin = separation_arcmin * math.cos(math.radians(position_angle))
        offsets.append(
            JupiterMoonOffset(
                name=label,
                east_arcmin=round(east_arcmin, 1),
                north_arcmin=round(north_arcmin, 1),
            )
        )

    return JupiterMoonsDetail(
        sampled_at=peak_at,
        moons=offsets,
    )


def compute_saturn_ring_tilt(
    observer: Observer,
    date_str: str,
    peak_at: str,
    timezone_name: str,
) -> tuple[float | None, str | None]:
    sample_time = _peak_time_from_hhmm(date_str, peak_at, timezone_name)
    if sample_time is None:
        return None, None

    day_start, day_end = calendar_day_bounds(date_str, timezone_name)
    if sample_time.ut < day_start.ut or sample_time.ut > day_end.ut:
        return None, None

    illumination = Illumination(Body.Saturn, sample_time)
    ring_tilt = illumination.ring_tilt
    if ring_tilt is None:
        return None, None

    tilt = round(ring_tilt, 1)
    if tilt < 2.0:
        note = "Edge-on"
    elif tilt > 20.0:
        note = "Wide open"
    else:
        note = "Moderately open"
    return tilt, note

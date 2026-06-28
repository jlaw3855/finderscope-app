"""Meteor shower catalog and radiant visibility during forecast dark windows."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path

from astronomy import Body, Horizon, Observer, Refraction, Time

from app.models.forecast import MeteorShowerHighlight
from app.services.astronomy_geometry import altitude_deg, is_in_nights_darkness, time_to_minutes
from app.services.astronomy_time import cached_zoneinfo, local_datetime_to_time

ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG = -18.0
SAMPLE_STEP_MINUTES = 30
METEOR_SHOWER_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "iau_meteor_showers.json"
)


@lru_cache(maxsize=1)
def load_meteor_shower_catalog() -> tuple[dict, ...]:
    if not METEOR_SHOWER_CATALOG_PATH.exists():
        return ()
    showers = json.loads(METEOR_SHOWER_CATALOG_PATH.read_text(encoding="utf-8"))
    return tuple(showers)


def showers_peaking_on(calendar_date: date) -> list[dict]:
    return [
        shower
        for shower in load_meteor_shower_catalog()
        if shower.get("peak_month") == calendar_date.month
        and shower.get("peak_day") == calendar_date.day
    ]


def _minutes_to_time(total_minutes: int) -> time:
    return time(total_minutes // 60, total_minutes % 60)


def radiant_altitude(
    observer: Observer,
    ra_hours: float,
    dec_deg: float,
    moment: Time,
) -> float:
    horizon = Horizon(moment, observer, ra_hours, dec_deg, Refraction.Normal)
    return horizon.altitude


def sun_below_astronomical_twilight(observer: Observer, moment: Time) -> bool:
    return altitude_deg(Body.Sun, observer, moment) < ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG


def _dark_window_sample_datetimes(
    day_date: str,
    night_begin: str,
    night_end: str,
    timezone_name: str,
) -> list[datetime]:
    tz = cached_zoneinfo(timezone_name)
    day = date.fromisoformat(day_date)
    begin_minutes = time_to_minutes(night_begin)
    end_minutes = time_to_minutes(night_end)

    if begin_minutes <= end_minutes:
        start = datetime.combine(day, _minutes_to_time(begin_minutes), tzinfo=tz)
        end = datetime.combine(day, _minutes_to_time(end_minutes), tzinfo=tz)
    else:
        start = datetime.combine(day, _minutes_to_time(begin_minutes), tzinfo=tz)
        end = datetime.combine(
            day + timedelta(days=1),
            _minutes_to_time(end_minutes),
            tzinfo=tz,
        )

    samples: list[datetime] = []
    current = start
    while current <= end:
        naive = current.replace(tzinfo=None)
        if is_in_nights_darkness(naive, day_date, night_begin, night_end):
            samples.append(current)
        current += timedelta(minutes=SAMPLE_STEP_MINUTES)
    return samples


def is_radiant_visible_during_dark_window(
    latitude: float,
    longitude: float,
    timezone_name: str,
    day_date: str,
    night_begin: str,
    night_end: str,
    ra_hours: float,
    dec_deg: float,
) -> bool:
    observer = Observer(latitude, longitude, 0.0)
    for sample_dt in _dark_window_sample_datetimes(
        day_date,
        night_begin,
        night_end,
        timezone_name,
    ):
        moment = local_datetime_to_time(sample_dt)
        if radiant_altitude(observer, ra_hours, dec_deg, moment) <= 0:
            continue
        if sun_below_astronomical_twilight(observer, moment):
            return True
    return False


def meteor_highlights_for_night(
    latitude: float,
    longitude: float,
    timezone_name: str,
    day_date: str,
    night_begin: str,
    night_end: str,
) -> list[MeteorShowerHighlight]:
    if not night_begin or not night_end:
        return []

    calendar_date = date.fromisoformat(day_date)
    highlights: list[MeteorShowerHighlight] = []
    for shower in showers_peaking_on(calendar_date):
        if not is_radiant_visible_during_dark_window(
            latitude,
            longitude,
            timezone_name,
            day_date,
            night_begin,
            night_end,
            shower["radiant_ra_hours"],
            shower["radiant_dec_deg"],
        ):
            continue
        highlights.append(
            MeteorShowerHighlight(
                id=shower["id"],
                name=shower["name"],
                zhr_nominal=shower.get("zhr_nominal"),
            )
        )
    return highlights

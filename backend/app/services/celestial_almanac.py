"""Rise, set, and transit times for the Sun, Moon, and planets."""

from __future__ import annotations

from astronomy import Body, Observer, SearchHourAngle, Time

from app.models.astronomy import CelestialAlmanacRow, CelestialDayAlmanac
from app.services.astronomy_time import calendar_day_bounds, time_to_local_hhmm
from app.services.planet_visibility import NAKED_EYE_BODIES, TELESCOPE_BODIES
from app.services.rise_set import collect_daily_rise_set

ALMANAC_BODIES: list[tuple[Body, str]] = [
    (Body.Sun, "Sun"),
    (Body.Moon, "Moon"),
    *NAKED_EYE_BODIES,
]


def _transit_for_body(
    body: Body,
    observer: Observer,
    day_start: Time,
    day_end: Time,
) -> tuple[Time | None, float | None]:
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    event = SearchHourAngle(body, observer, 0.0, day_start, span_days)
    if event is None:
        return None, None
    if event.time.ut < day_start.ut or event.time.ut > day_end.ut:
        return None, None
    return event.time, round(event.hor.altitude, 1)


def _almanac_row(
    body: Body,
    label: str,
    observer: Observer,
    day_start: Time,
    day_end: Time,
    timezone_name: str,
) -> CelestialAlmanacRow:
    rise_set = collect_daily_rise_set(body, observer, day_start, day_end)
    transit_time, transit_alt = _transit_for_body(body, observer, day_start, day_end)

    return CelestialAlmanacRow(
        body=label,
        rise_at=time_to_local_hhmm(rise_set.rise, timezone_name) if rise_set.rise else None,
        transit_at=time_to_local_hhmm(transit_time, timezone_name) if transit_time else None,
        set_at=time_to_local_hhmm(rise_set.set, timezone_name) if rise_set.set else None,
        transit_altitude_deg=transit_alt,
        always_up=rise_set.always_up,
        always_down=rise_set.always_down,
    )


def compute_celestial_almanac(
    latitude: float,
    longitude: float,
    timezone_name: str,
    dates: list[str],
    *,
    include_telescope_bodies: bool = True,
) -> list[CelestialDayAlmanac]:
    observer = Observer(latitude, longitude, 0.0)
    bodies = list(ALMANAC_BODIES)
    if include_telescope_bodies:
        bodies.extend(TELESCOPE_BODIES)

    results: list[CelestialDayAlmanac] = []
    for date_str in dates:
        day_start, day_end = calendar_day_bounds(date_str, timezone_name)
        rows = [
            _almanac_row(body, label, observer, day_start, day_end, timezone_name)
            for body, label in bodies
        ]
        results.append(CelestialDayAlmanac(date=date_str, rows=rows))
    return results

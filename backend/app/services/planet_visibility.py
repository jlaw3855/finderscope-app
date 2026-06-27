"""Planet above-horizon visibility for forecast calendar days."""

from __future__ import annotations

import astronomy
from astronomy import Body, Direction, Equator, Horizon, Illumination, Observer, Refraction, SearchRiseSet, Time

from app.models.astronomy import PlanetDayVisibility, PlanetVisibilityRow, VisibilityWindow
from app.services.astronomy_time import (
    calendar_day_bounds,
    time_to_local_hhmm,
    time_to_utc_datetime,
)

NAKED_EYE_BODIES: list[tuple[Body, str]] = [
    (Body.Mercury, "Mercury"),
    (Body.Venus, "Venus"),
    (Body.Mars, "Mars"),
    (Body.Jupiter, "Jupiter"),
    (Body.Saturn, "Saturn"),
]

TELESCOPE_BODIES: list[tuple[Body, str]] = [
    (Body.Uranus, "Uranus"),
    (Body.Neptune, "Neptune"),
]

SAMPLE_INTERVAL_MINUTES = 30


def _altitude_deg(body: Body, observer: Observer, moment: Time) -> float:
    equator = Equator(body, moment, observer, ofdate=True, aberration=True)
    horizon = Horizon(moment, observer, equator.ra, equator.dec, Refraction.Normal)
    return horizon.altitude


def _clip_window(
    window_start: Time,
    window_end: Time,
    day_start: Time,
    day_end: Time,
) -> tuple[Time, Time] | None:
    start_ut = max(window_start.ut, day_start.ut)
    end_ut = min(window_end.ut, day_end.ut)
    if start_ut > end_ut:
        return None
    return Time(start_ut), Time(end_ut)


def _collect_day_windows(
    body: Body,
    observer: Observer,
    day_start: Time,
    day_end: Time,
) -> list[tuple[Time, Time]]:
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    windows: list[tuple[Time, Time]] = []

    alt_at_start = _altitude_deg(body, observer, day_start)
    cursor = day_start

    if alt_at_start > 0:
        set_time = SearchRiseSet(body, observer, Direction.Set, day_start, span_days)
        if set_time is None or set_time.ut > day_end.ut:
            clipped = _clip_window(day_start, day_end, day_start, day_end)
            return [clipped] if clipped else []
        clipped = _clip_window(day_start, set_time, day_start, day_end)
        if clipped:
            windows.append(clipped)
        cursor = set_time

    while cursor.ut <= day_end.ut:
        rise = SearchRiseSet(body, observer, Direction.Rise, cursor, span_days)
        if rise is None or rise.ut > day_end.ut:
            break
        set_time = SearchRiseSet(body, observer, Direction.Set, rise, span_days)
        if set_time is None:
            clipped = _clip_window(rise, day_end, day_start, day_end)
            if clipped:
                windows.append(clipped)
            break
        clipped = _clip_window(rise, set_time, day_start, day_end)
        if clipped:
            windows.append(clipped)
        if set_time.ut >= day_end.ut:
            break
        cursor = set_time

    return windows


def _peak_within_windows(
    body: Body,
    observer: Observer,
    windows: list[tuple[Time, Time]],
    timezone_name: str,
) -> tuple[float | None, str | None, float | None]:
    if not windows:
        return None, None, None

    best_alt = None
    best_time: Time | None = None
    step_days = SAMPLE_INTERVAL_MINUTES / (24.0 * 60.0)

    for window_start, window_end in windows:
        sample = window_start
        while sample.ut <= window_end.ut:
            alt = _altitude_deg(body, observer, sample)
            if best_alt is None or alt > best_alt:
                best_alt = alt
                best_time = sample
            sample = Time.AddDays(sample, step_days)

    if best_time is None or best_alt is None:
        return None, None, None

    magnitude = Illumination(body, best_time).mag
    return best_alt, time_to_local_hhmm(best_time, timezone_name), magnitude


def _visibility_row(
    body: Body,
    label: str,
    observer: Observer,
    day_start: Time,
    day_end: Time,
    timezone_name: str,
) -> PlanetVisibilityRow:
    raw_windows = _collect_day_windows(body, observer, day_start, day_end)
    windows = [
        VisibilityWindow(
            start=time_to_local_hhmm(start, timezone_name),
            end=time_to_local_hhmm(end, timezone_name),
        )
        for start, end in raw_windows
    ]
    peak_alt, peak_at, magnitude = _peak_within_windows(
        body, observer, raw_windows, timezone_name
    )
    return PlanetVisibilityRow(
        body=label,
        visible=len(windows) > 0,
        windows=windows,
        peak_altitude_deg=peak_alt,
        peak_at=peak_at,
        magnitude=magnitude,
    )


def compute_planet_visibility(
    latitude: float,
    longitude: float,
    timezone_name: str,
    dates: list[str],
    *,
    include_telescope_bodies: bool = True,
) -> list[PlanetDayVisibility]:
    observer = Observer(latitude, longitude, 0.0)
    bodies = list(NAKED_EYE_BODIES)
    if include_telescope_bodies:
        bodies.extend(TELESCOPE_BODIES)

    results: list[PlanetDayVisibility] = []
    for date_str in dates:
        day_start, day_end = calendar_day_bounds(date_str, timezone_name)
        planets = [
            _visibility_row(body, label, observer, day_start, day_end, timezone_name)
            for body, label in bodies
        ]
        results.append(PlanetDayVisibility(date=date_str, planets=planets))
    return results

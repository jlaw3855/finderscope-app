"""Planet above-horizon visibility for forecast calendar days."""

from __future__ import annotations

from astronomy import (
    Body,
    Direction,
    Illumination,
    Observer,
    SearchAltitude,
    SearchRiseSet,
    Time,
)

from app.models.astronomy import (
    PlanetDayVisibility,
    PlanetVisibilityRow,
    VisibilityWindow,
)
from app.services.astronomy_geometry import altitude_deg
from app.services.astronomy_time import (
    calendar_day_bounds,
    time_to_local_hhmm,
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

# * Sun altitude thresholds for observable sky darkness (degrees below horizon).
CIVIL_TWILIGHT_SUN_ALTITUDE_DEG = -6.0
ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG = -18.0


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


def _collect_above_horizon_windows(
    body: Body,
    observer: Observer,
    day_start: Time,
    day_end: Time,
) -> list[tuple[Time, Time]]:
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    windows: list[tuple[Time, Time]] = []

    alt_at_start = altitude_deg(body, observer, day_start)
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


def _collect_sun_below_windows(
    observer: Observer,
    day_start: Time,
    day_end: Time,
    altitude_limit: float,
) -> list[tuple[Time, Time]]:
    """Intervals on the calendar day when the Sun is below altitude_limit."""
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    windows: list[tuple[Time, Time]] = []

    alt_at_start = altitude_deg(Body.Sun, observer, day_start)
    cursor = day_start

    if alt_at_start < altitude_limit:
        rise = SearchAltitude(
            Body.Sun, observer, Direction.Rise, day_start, span_days, altitude_limit
        )
        if rise is None or rise.ut > day_end.ut:
            clipped = _clip_window(day_start, day_end, day_start, day_end)
            return [clipped] if clipped else []
        clipped = _clip_window(day_start, rise, day_start, day_end)
        if clipped:
            windows.append(clipped)
        cursor = rise

    while cursor.ut <= day_end.ut:
        set_time = SearchAltitude(
            Body.Sun, observer, Direction.Set, cursor, span_days, altitude_limit
        )
        if set_time is None or set_time.ut > day_end.ut:
            break
        rise = SearchAltitude(
            Body.Sun, observer, Direction.Rise, set_time, span_days, altitude_limit
        )
        if rise is None:
            clipped = _clip_window(set_time, day_end, day_start, day_end)
            if clipped:
                windows.append(clipped)
            break
        clipped = _clip_window(set_time, rise, day_start, day_end)
        if clipped:
            windows.append(clipped)
        if rise.ut >= day_end.ut:
            break
        cursor = rise

    return windows


def _intersect_windows(
    left: list[tuple[Time, Time]],
    right: list[tuple[Time, Time]],
) -> list[tuple[Time, Time]]:
    intersections: list[tuple[Time, Time]] = []
    for left_start, left_end in left:
        for right_start, right_end in right:
            start_ut = max(left_start.ut, right_start.ut)
            end_ut = min(left_end.ut, right_end.ut)
            if start_ut <= end_ut:
                intersections.append((Time(start_ut), Time(end_ut)))
    return intersections


def _merge_time_windows(windows: list[tuple[Time, Time]]) -> list[tuple[Time, Time]]:
    if not windows:
        return []

    sorted_windows = sorted(windows, key=lambda entry: entry[0].ut)
    merged: list[tuple[Time, Time]] = [sorted_windows[0]]

    for window_start, window_end in sorted_windows[1:]:
        last_start, last_end = merged[-1]
        if window_start.ut <= last_end.ut:
            merged[-1] = (last_start, Time(max(last_end.ut, window_end.ut)))
            continue
        merged.append((window_start, window_end))

    return merged


def _to_visibility_windows(
    windows: list[tuple[Time, Time]],
    timezone_name: str,
) -> list[VisibilityWindow]:
    return [
        VisibilityWindow(
            start=time_to_local_hhmm(start, timezone_name),
            end=time_to_local_hhmm(end, timezone_name),
        )
        for start, end in windows
    ]


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
            alt = altitude_deg(body, observer, sample)
            if best_alt is None or alt > best_alt:
                best_alt = alt
                best_time = sample
            sample = Time.AddDays(sample, step_days)

    if best_time is None or best_alt is None:
        return None, None, None

    magnitude = round(Illumination(body, best_time).mag, 1)
    return round(best_alt, 1), time_to_local_hhmm(best_time, timezone_name), magnitude


def _visibility_row(
    body: Body,
    label: str,
    observer: Observer,
    day_start: Time,
    day_end: Time,
    timezone_name: str,
    *,
    civil_sun_windows: list[tuple[Time, Time]],
    astronomical_sun_windows: list[tuple[Time, Time]],
) -> PlanetVisibilityRow:
    horizon_windows = _collect_above_horizon_windows(body, observer, day_start, day_end)

    civil_windows = _merge_time_windows(_intersect_windows(horizon_windows, civil_sun_windows))
    astronomical_windows = _merge_time_windows(
        _intersect_windows(horizon_windows, astronomical_sun_windows)
    )

    peak_windows = astronomical_windows or civil_windows
    peak_alt, peak_at, magnitude = _peak_within_windows(
        body, observer, peak_windows, timezone_name
    )

    return PlanetVisibilityRow(
        body=label,
        visible=len(civil_windows) > 0,
        windows_civil=_to_visibility_windows(civil_windows, timezone_name),
        windows_astronomical=_to_visibility_windows(astronomical_windows, timezone_name),
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
        civil_sun_windows = _collect_sun_below_windows(
            observer, day_start, day_end, CIVIL_TWILIGHT_SUN_ALTITUDE_DEG
        )
        astronomical_sun_windows = _collect_sun_below_windows(
            observer, day_start, day_end, ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG
        )
        planets = [
            _visibility_row(
                body,
                label,
                observer,
                day_start,
                day_end,
                timezone_name,
                civil_sun_windows=civil_sun_windows,
                astronomical_sun_windows=astronomical_sun_windows,
            )
            for body, label in bodies
        ]
        results.append(PlanetDayVisibility(date=date_str, planets=planets))
    return results

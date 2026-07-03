"""Shared twilight and visibility window helpers."""

from __future__ import annotations

from astronomy import Body, Direction, Observer, SearchAltitude, Time

from app.models.astronomy import VisibilityWindow
from app.services.astronomy_geometry import altitude_deg
from app.services.astronomy_time import time_to_local_hhmm

# * Sun altitude thresholds for observable sky darkness (degrees below horizon).
CIVIL_TWILIGHT_SUN_ALTITUDE_DEG = -6.0
ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG = -18.0

SAMPLE_INTERVAL_MINUTES = 30


def clip_window(
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


def collect_sun_below_windows(
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
            clipped = clip_window(day_start, day_end, day_start, day_end)
            return [clipped] if clipped else []
        clipped = clip_window(day_start, rise, day_start, day_end)
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
            clipped = clip_window(set_time, day_end, day_start, day_end)
            if clipped:
                windows.append(clipped)
            break
        clipped = clip_window(set_time, rise, day_start, day_end)
        if clipped:
            windows.append(clipped)
        if rise.ut >= day_end.ut:
            break
        cursor = rise

    return windows


def intersect_windows(
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


def merge_time_windows(windows: list[tuple[Time, Time]]) -> list[tuple[Time, Time]]:
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


def to_visibility_windows(
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

"""Rise and set event helpers for moving bodies."""

from __future__ import annotations

from dataclasses import dataclass

from astronomy import Body, Direction, Observer, SearchRiseSet, Time

from app.services.astronomy_geometry import altitude_deg
from app.services.visibility_windows import clip_window


@dataclass(frozen=True)
class DailyRiseSet:
    rise: Time | None
    set: Time | None
    always_up: bool = False
    always_down: bool = False


def collect_above_horizon_windows(
    body: Body,
    observer: Observer,
    day_start: Time,
    day_end: Time,
) -> list[tuple[Time, Time]]:
    """Return clipped above-horizon intervals for a body on a calendar day."""
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    windows: list[tuple[Time, Time]] = []

    alt_at_start = altitude_deg(body, observer, day_start)
    cursor = day_start

    if alt_at_start > 0:
        set_time = SearchRiseSet(body, observer, Direction.Set, day_start, span_days)
        if set_time is None or set_time.ut > day_end.ut:
            clipped = clip_window(day_start, day_end, day_start, day_end)
            return [clipped] if clipped else []
        clipped = clip_window(day_start, set_time, day_start, day_end)
        if clipped:
            windows.append(clipped)
        cursor = set_time

    while cursor.ut <= day_end.ut:
        rise = SearchRiseSet(body, observer, Direction.Rise, cursor, span_days)
        if rise is None or rise.ut > day_end.ut:
            break
        set_time = SearchRiseSet(body, observer, Direction.Set, rise, span_days)
        if set_time is None:
            clipped = clip_window(rise, day_end, day_start, day_end)
            if clipped:
                windows.append(clipped)
            break
        clipped = clip_window(rise, set_time, day_start, day_end)
        if clipped:
            windows.append(clipped)
        if set_time.ut >= day_end.ut:
            break
        cursor = set_time

    return windows


def collect_daily_rise_set(
    body: Body,
    observer: Observer,
    day_start: Time,
    day_end: Time,
) -> DailyRiseSet:
    """Return the primary rise and set events for a body on a calendar day."""
    span_days = max((day_end.ut - day_start.ut) + 1.0, 1.5)
    alt_at_start = altitude_deg(body, observer, day_start)

    if alt_at_start > 0:
        set_time = SearchRiseSet(body, observer, Direction.Set, day_start, span_days)
        if set_time is None or set_time.ut > day_end.ut:
            return DailyRiseSet(rise=None, set=None, always_up=True)
        if set_time.ut < day_start.ut:
            return DailyRiseSet(rise=None, set=None, always_up=True)
        return DailyRiseSet(rise=None, set=set_time)

    rise = SearchRiseSet(body, observer, Direction.Rise, day_start, span_days)
    if rise is None or rise.ut > day_end.ut:
        return DailyRiseSet(rise=None, set=None, always_down=True)

    set_time = SearchRiseSet(body, observer, Direction.Set, rise, span_days)
    if set_time is None or set_time.ut > day_end.ut:
        return DailyRiseSet(rise=rise, set=None)
    return DailyRiseSet(rise=rise, set=set_time)

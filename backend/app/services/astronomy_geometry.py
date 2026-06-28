"""Shared astronomy geometry helpers for darkness windows and altitudes."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from astronomy import Body, Equator, Horizon, Observer, Refraction, Time


def altitude_deg(body: Body, observer: Observer, moment: Time) -> float:
    equator = Equator(body, moment, observer, ofdate=True, aberration=True)
    horizon = Horizon(moment, observer, equator.ra, equator.dec, Refraction.Normal)
    return horizon.altitude


def parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def time_to_minutes(value: str) -> int:
    hour, minute = parse_hhmm(value)
    return hour * 60 + minute


def is_in_nights_darkness(
    hour_dt: datetime,
    day_date: str,
    night_begin: str,
    night_end: str,
) -> bool:
    """
    Return True when the hour belongs to this night's darkness window only.

    Includes evening hours on day_date from night_begin onward and early-morning
    hours on the next calendar day before night_end. Excludes the previous
    night's tail that falls on day_date before night_begin.
    """
    begin_minutes = time_to_minutes(night_begin)
    end_minutes = time_to_minutes(night_end)
    hour_minutes = hour_dt.hour * 60 + hour_dt.minute
    hour_date = hour_dt.date()
    day = date.fromisoformat(day_date)
    next_day = day + timedelta(days=1)

    if begin_minutes <= end_minutes:
        return hour_date == day and begin_minutes <= hour_minutes < end_minutes

    if hour_date == day and hour_minutes >= begin_minutes:
        return True
    if hour_date == next_day and hour_minutes < end_minutes:
        return True
    return False

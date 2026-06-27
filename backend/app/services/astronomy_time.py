"""Time conversion helpers for astronomy-engine."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import astronomy
from astronomy import Time


def parse_calendar_date(date_str: str) -> date:
    return date.fromisoformat(date_str)


def local_datetime_to_time(value: datetime) -> Time:
    utc = value.astimezone(timezone.utc)
    return Time.Make(
        utc.year,
        utc.month,
        utc.day,
        utc.hour,
        utc.minute,
        int(utc.second),
    )


def time_to_utc_datetime(value: Time) -> datetime:
    return value.Utc().replace(tzinfo=timezone.utc)


def time_to_local_hhmm(value: Time, timezone_name: str) -> str:
    local = time_to_utc_datetime(value).astimezone(ZoneInfo(timezone_name))
    return local.strftime("%H:%M")


def calendar_day_bounds(date_str: str, timezone_name: str) -> tuple[Time, Time]:
    day = parse_calendar_date(date_str)
    tz = ZoneInfo(timezone_name)
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    end_local = datetime.combine(day, time(23, 59, 59), tzinfo=tz)
    return local_datetime_to_time(start_local), local_datetime_to_time(end_local)


def utc_now_time() -> Time:
    return Time.Now()

"""Merge astronomy darkness windows with hourly weather into stargazing scores."""

import bisect
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.models.forecast import (
    BestHourWindow,
    CloudCoverBreakdown,
    ForecastResponse,
    HourlyScore,
    LocationInfo,
    NightForecast,
    PrecipitationBreakdown,
    TimeWindow,
)
from app.services import meteor_showers, moon_position
from app.services.astronomy_geometry import (
    is_in_nights_darkness as _is_in_nights_darkness,
)
from app.services.astronomy_geometry import time_to_minutes as _time_to_minutes
from app.services.seventimer import (
    AstroIndex,
    build_astro_index,
    lookup_astro_at,
)

# * WMO weather codes that indicate poor stargazing conditions.
BAD_WEATHER_CODES = {
    45, 48,  # fog
    51, 53, 55, 56, 57,  # drizzle
    61, 63, 65, 66, 67,  # rain
    71, 73, 75, 77,  # snow
    80, 81, 82,  # rain showers
    85, 86,  # snow showers
    95, 96, 99,  # thunderstorm
}

SCORE_STEP_MINUTES = 30

CONTINUOUS_WEATHER_FIELDS = [
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "precipitation_probability",
    "dew_point_2m",
    "temperature_2m",
]

HOURLY_WEATHER_FIELDS = [
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "precipitation",
    "precipitation_probability",
    "weather_code",
    "dew_point_2m",
    "temperature_2m",
]


SYNODIC_MONTH_DAYS = 29.53059

WANING_PHASES = frozenset(
    {"WANING_GIBBOUS", "LAST_QUARTER", "WANING_CRESCENT"}
)

PHASE_LUNAR_AGE_ESTIMATES: dict[str, float] = {
    "NEW_MOON": 0.0,
    "WAXING_CRESCENT": 5.0,
    "FIRST_QUARTER": 7.4,
    "WAXING_GIBBOUS": 11.0,
    "FULL_MOON": 14.77,
    "WANING_GIBBOUS": 18.5,
    "LAST_QUARTER": 22.1,
    "WANING_CRESCENT": 26.0,
}

# * Approximate illumination when interpolation cannot be applied.
PHASE_ILLUMINATION_ESTIMATES: dict[str, float] = {
    "NEW_MOON": 0.0,
    "WAXING_CRESCENT": 25.0,
    "FIRST_QUARTER": 50.0,
    "WAXING_GIBBOUS": 75.0,
    "FULL_MOON": 100.0,
    "WANING_GIBBOUS": 75.0,
    "LAST_QUARTER": 50.0,
    "WANING_CRESCENT": 25.0,
}


@dataclass(frozen=True)
class MoonIlluminationAnchor:
    """Single-day API anchor used to interpolate illumination on later nights."""

    anchor_date: date
    illumination: float
    lunar_age_days: float


def _parse_illumination(raw: object) -> float | None:
    """Parse moon illumination; IPGeolocation uses negative values for waning phases."""
    if raw is None:
        return None
    try:
        return abs(float(raw))
    except (TypeError, ValueError):
        return None


def _is_waning_phase(moon_phase: str, raw_illumination: object) -> bool:
    if raw_illumination is not None:
        try:
            return float(raw_illumination) < 0
        except (TypeError, ValueError):
            pass
    return moon_phase.upper() in WANING_PHASES


def _illumination_fraction(illumination_pct: float) -> float:
    return max(0.0, min(1.0, illumination_pct / 100.0))


def _lunar_age_from_illumination(illumination_pct: float, is_waning: bool) -> float:
    """Infer lunar age (days since new moon) from illuminated fraction and wax/wane side."""
    fraction = _illumination_fraction(illumination_pct)
    if fraction <= 0.0:
        return 0.0
    if fraction >= 1.0:
        return SYNODIC_MONTH_DAYS / 2

    offset = (SYNODIC_MONTH_DAYS / (2 * math.pi)) * math.acos(1 - 2 * fraction)
    if is_waning:
        return SYNODIC_MONTH_DAYS - offset
    return offset


def _illumination_from_lunar_age(lunar_age_days: float) -> float:
    """Convert lunar age to an illuminated percentage using a sinusoidal synodic model."""
    age = lunar_age_days % SYNODIC_MONTH_DAYS
    fraction = (1 - math.cos(2 * math.pi * age / SYNODIC_MONTH_DAYS)) / 2
    return round(fraction * 100, 1)


def _estimate_illumination_from_phase(moon_phase: str) -> float:
    age = PHASE_LUNAR_AGE_ESTIMATES.get(moon_phase.upper())
    if age is not None:
        return _illumination_from_lunar_age(age)
    return PHASE_ILLUMINATION_ESTIMATES.get(moon_phase.upper(), 50.0)


def _moon_anchor_from_single_day(location_data: dict) -> MoonIlluminationAnchor | None:
    """Build an interpolation anchor from the initial single-day astronomy lookup."""
    astronomy = location_data.get("astronomy", {})
    day_date_raw = astronomy.get("date")
    raw_illumination = astronomy.get("moon_illumination_percentage")
    illumination = _parse_illumination(raw_illumination)
    if not day_date_raw or illumination is None:
        return None

    moon_phase = astronomy.get("moon_phase", "UNKNOWN")
    is_waning = _is_waning_phase(moon_phase, raw_illumination)
    lunar_age = _lunar_age_from_illumination(illumination, is_waning)

    return MoonIlluminationAnchor(
        anchor_date=datetime.fromisoformat(day_date_raw).date(),
        illumination=illumination,
        lunar_age_days=lunar_age,
    )


def _interpolate_illumination(
    anchor: MoonIlluminationAnchor,
    day_date: str,
    moon_phase: str,
) -> float:
    """Advance the lunar model from the anchor date and return estimated illumination."""
    target_date = datetime.fromisoformat(day_date).date()
    days_forward = (target_date - anchor.anchor_date).days

    if days_forward < 0:
        return _estimate_illumination_from_phase(moon_phase)

    if days_forward == 0:
        return anchor.illumination

    return _illumination_from_lunar_age(anchor.lunar_age_days + days_forward)


def _resolve_moon_illumination(
    day: dict,
    anchor: MoonIlluminationAnchor | None,
    day_date: str,
) -> float:
    """
    Resolve moon illumination using time series data, forward interpolation from
    the single-day anchor, then phase-based estimation as a fallback.
    """
    illumination = _parse_illumination(day.get("moon_illumination_percentage"))
    if illumination is not None:
        return illumination

    moon_phase = day.get("moon_phase", "UNKNOWN")

    if anchor is not None:
        return _interpolate_illumination(anchor, day_date, moon_phase)

    return _estimate_illumination_from_phase(moon_phase)


def _parse_time(time_str: str) -> tuple[int, int]:
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def _rating_from_score(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


def _weather_penalty(weather_code: float | None) -> float:
    if weather_code is None:
        return 50.0
    if int(weather_code) in BAD_WEATHER_CODES:
        return 0.0
    return 100.0


def _parse_moon_event(time_str: object) -> int | None:
    """Parse moonrise/moonset HH:mm into minutes; None when absent or -:-."""
    if not time_str or time_str == "-:-":
        return None
    try:
        return _time_to_minutes(str(time_str))
    except (ValueError, IndexError):
        return None


def _parse_moon_time_display(raw: object) -> str | None:
    if not raw or raw == "-:-":
        return None
    return str(raw)


def _is_moon_up_at_minutes(minutes: int, rise: int | None, set_: int | None) -> bool | None:
    """Return whether the moon is above the horizon; None when timing is unknown."""
    if rise is None and set_ is None:
        return None
    if rise is None:
        return minutes < set_
    if set_ is None:
        return minutes >= rise
    if rise < set_:
        return rise <= minutes < set_
    return minutes >= rise or minutes < set_


def _is_moon_up(hour_dt: datetime, astronomy_by_date: dict[str, dict]) -> bool | None:
    """Determine if the moon is above the horizon for a given hour."""
    day_astronomy = astronomy_by_date.get(hour_dt.date().isoformat())
    if day_astronomy is None:
        return None

    rise = _parse_moon_event(day_astronomy.get("moonrise"))
    set_ = _parse_moon_event(day_astronomy.get("moonset"))
    minutes = hour_dt.hour * 60 + hour_dt.minute
    result = _is_moon_up_at_minutes(minutes, rise, set_)
    if result is not None:
        return result

    prev_day = astronomy_by_date.get((hour_dt.date() - timedelta(days=1)).isoformat())
    if prev_day is None:
        return None

    prev_rise = _parse_moon_event(prev_day.get("moonrise"))
    prev_set = _parse_moon_event(prev_day.get("moonset"))
    if prev_rise is None:
        return None

    if prev_set is not None and prev_rise < prev_set:
        return None

    if set_ is not None:
        return minutes < set_
    if prev_set is None:
        return True
    return None


def _effective_moon_illumination(
    hour_dt: datetime,
    moon_illumination: float,
    astronomy_by_date: dict[str, dict],
    latitude: float,
    longitude: float,
    timezone: str,
) -> tuple[float, bool | None, float | None]:
    """Scale phase illumination by moon altitude; fall back to rise/set when needed."""
    sample_dt = moon_position.sample_interval_midpoint(hour_dt, SCORE_STEP_MINUTES)
    try:
        altitude = moon_position.moon_altitude_deg(
            latitude,
            longitude,
            sample_dt,
            timezone,
        )
        effective = moon_position.effective_moon_illumination(moon_illumination, altitude)
        moon_up = altitude > 0
        return effective, moon_up, round(altitude, 1)
    except Exception:
        moon_up = _is_moon_up(hour_dt, astronomy_by_date)
        if moon_up is False:
            return 0.0, False, None
        if moon_up is True:
            return moon_illumination, True, None
        return moon_illumination, None, None


def _resolve_night_moon_times(
    day: dict,
    astronomy_by_date: dict[str, dict],
) -> tuple[str | None, str | None]:
    """Moonrise on the night date; moonset from the following morning when available."""
    day_date = day.get("date", "")
    moonrise = _parse_moon_time_display(day.get("moonrise"))

    next_date = (datetime.fromisoformat(day_date).date() + timedelta(days=1)).isoformat()
    next_day = astronomy_by_date.get(next_date, {})
    moonset = _parse_moon_time_display(next_day.get("moonset"))
    if moonset is None:
        moonset = _parse_moon_time_display(day.get("moonset"))

    return moonrise, moonset


def _visibility_score(visibility: float | None) -> float:
    if visibility is None:
        return 50.0
    return min(visibility / 10000.0, 1.0) * 100.0


def _hour_score(
    cloud_cover: float | None,
    visibility: float | None,
    moon_illumination: float,
    precipitation: float | None,
    weather_code: float | None,
) -> int:
    cloud = cloud_cover if cloud_cover is not None else 100.0
    cloud_score = max(0.0, 100.0 - cloud)

    moon_score = max(0.0, 100.0 - abs(moon_illumination))

    precip_penalty = 0.0
    if precipitation is not None and precipitation > 0:
        precip_penalty = min(precipitation * 20.0, 100.0)
    weather_score = _weather_penalty(weather_code)
    precip_score = max(0.0, weather_score - precip_penalty)

    total = (
        cloud_score * 0.40
        + _visibility_score(visibility) * 0.25
        + moon_score * 0.25
        + precip_score * 0.10
    )
    return int(round(max(0.0, min(100.0, total))))


def _night_darkness_bounds(
    day_date: str,
    night_begin: str,
    night_end: str,
) -> tuple[datetime, datetime]:
    day = datetime.fromisoformat(day_date).date()
    begin_h, begin_m = _parse_time(night_begin)
    end_h, end_m = _parse_time(night_end)
    begin_minutes = begin_h * 60 + begin_m
    end_minutes = end_h * 60 + end_m

    start = datetime.combine(day, datetime.min.time()).replace(hour=begin_h, minute=begin_m)
    if begin_minutes <= end_minutes:
        end = datetime.combine(day, datetime.min.time()).replace(hour=end_h, minute=end_m)
    else:
        end = datetime.combine(day + timedelta(days=1), datetime.min.time()).replace(
            hour=end_h, minute=end_m
        )
    return start, end


def _darkness_slots_for_night(
    day_date: str,
    night_begin: str,
    night_end: str,
    score_slots: list[datetime],
) -> list[datetime]:
    """Return score grid slots belonging to this night's darkness window."""
    if not score_slots:
        return []

    dark_start, dark_end = _night_darkness_bounds(day_date, night_begin, night_end)
    start_idx = bisect.bisect_left(score_slots, dark_start)
    end_idx = bisect.bisect_right(score_slots, dark_end)

    return [
        slot_dt
        for slot_dt in score_slots[start_idx:end_idx]
        if _is_in_nights_darkness(slot_dt, day_date, night_begin, night_end)
    ]


def _find_best_hours(hourly: list[HourlyScore], threshold: int = 70) -> list[BestHourWindow]:
    if not hourly:
        return []

    windows: list[BestHourWindow] = []
    current_start: str | None = None
    current_end: str | None = None
    current_scores: list[int] = []

    for entry in hourly:
        if entry.score >= threshold:
            if current_start is None:
                current_start = entry.time
            current_end = entry.time
            current_scores.append(entry.score)
        elif current_start is not None:
            windows.append(
                BestHourWindow(
                    start=current_start,
                    end=current_end or current_start,
                    score=int(round(sum(current_scores) / len(current_scores))),
                )
            )
            current_start = None
            current_end = None
            current_scores = []

    if current_start is not None:
        windows.append(
            BestHourWindow(
                start=current_start,
                end=current_end or current_start,
                score=int(round(sum(current_scores) / len(current_scores))),
            )
        )

    return windows


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _build_daily_lookup(weather_data: dict) -> dict[str, dict[str, float | None]]:
    daily = weather_data.get("daily", {})
    dates = daily.get("time", [])
    lookup: dict[str, dict[str, float | None]] = {}

    for index, day_date in enumerate(dates):
        lookup[day_date] = {
            "temperature_high": _value_at(daily, "temperature_2m_max", index),
            "temperature_low": _value_at(daily, "temperature_2m_min", index),
            "precipitation_sum": _value_at(daily, "precipitation_sum", index),
        }

    return lookup


def _value_at(block: dict, key: str, index: int) -> float | None:
    values = block.get(key, [])
    if index >= len(values):
        return None
    value = values[index]
    return float(value) if value is not None else None


def _summarize_hourly_weather(hourly_scores: list[HourlyScore]) -> tuple[CloudCoverBreakdown, PrecipitationBreakdown]:
    cloud = CloudCoverBreakdown(
        total=_average([entry.cloud_cover for entry in hourly_scores if entry.cloud_cover is not None]),
        low=_average([entry.cloud_cover_low for entry in hourly_scores if entry.cloud_cover_low is not None]),
        mid=_average([entry.cloud_cover_mid for entry in hourly_scores if entry.cloud_cover_mid is not None]),
        high=_average([entry.cloud_cover_high for entry in hourly_scores if entry.cloud_cover_high is not None]),
    )

    precip_values = [entry.precipitation for entry in hourly_scores if entry.precipitation is not None]
    prob_values = [
        entry.precipitation_probability
        for entry in hourly_scores
        if entry.precipitation_probability is not None
    ]

    precipitation = PrecipitationBreakdown(
        total_mm=sum(precip_values) if precip_values else None,
        max_hourly_mm=max(precip_values) if precip_values else None,
        max_probability=max(prob_values) if prob_values else None,
    )

    return cloud, precipitation


def _iso_time_key(dt: datetime) -> str:
    return dt.replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def _index_weather_block(
    block: dict,
    fields: list[str],
) -> dict[str, dict[str, float | None]]:
    times: list[str] = block.get("time", [])
    indexed: dict[str, dict[str, float | None]] = {}
    for index, time_key in enumerate(times):
        indexed[time_key] = {field: _value_at(block, field, index) for field in fields}
    return indexed


def _lerp_float(a: float | None, b: float | None, t: float) -> float | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return a + (b - a) * t


def _half_hour_slots_from_hourly_times(hourly_times: list[str]) -> list[datetime]:
    if not hourly_times:
        return []

    start = datetime.fromisoformat(hourly_times[0])
    end = datetime.fromisoformat(hourly_times[-1])
    start_slot = start.replace(minute=(start.minute // 30) * 30, second=0, microsecond=0)

    slots: list[datetime] = []
    current = start_slot
    while current <= end:
        slots.append(current)
        current += timedelta(minutes=SCORE_STEP_MINUTES)
    return slots


def _detect_score_step(weather_data: dict) -> int:
    hourly_times = weather_data.get("hourly", {}).get("time", [])
    if hourly_times:
        return SCORE_STEP_MINUTES
    minutely_times = weather_data.get("minutely_15", {}).get("time", [])
    if len(minutely_times) >= 4:
        return SCORE_STEP_MINUTES
    return 60


def _slot_precip_from_minutely(
    slot_dt: datetime,
    minutely_by_time: dict[str, dict[str, float | None]],
) -> float | None:
    first_key = _iso_time_key(slot_dt + timedelta(minutes=15))
    second_key = _iso_time_key(slot_dt + timedelta(minutes=30))
    first = minutely_by_time.get(first_key, {}).get("precipitation")
    second = minutely_by_time.get(second_key, {}).get("precipitation")
    if first is None and second is None:
        return None
    return (first or 0.0) + (second or 0.0)


def _weather_at_slot(
    slot_dt: datetime,
    minutely_by_time: dict[str, dict[str, float | None]],
    hourly_by_time: dict[str, dict[str, float | None]],
) -> dict[str, float | None]:
    slot_key = _iso_time_key(slot_dt)
    minutely = minutely_by_time.get(slot_key)

    if minutely is not None:
        wx = dict(minutely)
        slot_precip = _slot_precip_from_minutely(slot_dt, minutely_by_time)
        if slot_precip is not None:
            wx["precipitation"] = slot_precip
        return wx

    hour_key = _iso_time_key(slot_dt.replace(minute=0))
    hour_wx = hourly_by_time.get(hour_key)
    if hour_wx is None:
        return {field: None for field in HOURLY_WEATHER_FIELDS}

    if slot_dt.minute == 0:
        return dict(hour_wx)

    next_hour_key = _iso_time_key(slot_dt.replace(minute=0) + timedelta(hours=1))
    next_wx = hourly_by_time.get(next_hour_key, {})
    wx: dict[str, float | None] = {}

    for field in CONTINUOUS_WEATHER_FIELDS:
        wx[field] = _lerp_float(hour_wx.get(field), next_wx.get(field), 0.5)

    hour_precip = hour_wx.get("precipitation")
    wx["precipitation"] = hour_precip / 2.0 if hour_precip is not None else None
    wx["weather_code"] = hour_wx.get("weather_code")
    return wx


def _dark_window_from_astronomy_day(day: dict) -> TimeWindow | None:
    night_begin = day.get("night_begin")
    night_end = day.get("night_end") or day.get("morning", {}).get("astronomical_twilight_end")
    if not night_begin or not night_end:
        return None
    return TimeWindow(start=night_begin, end=night_end)


def _in_forecast_window(
    day_date: str,
    forecast_start: date | None,
    forecast_end: date | None,
) -> bool:
    if forecast_start is None and forecast_end is None:
        return True
    if not day_date:
        return False
    parsed = date.fromisoformat(day_date)
    if forecast_start is not None and parsed < forecast_start:
        return False
    if forecast_end is not None and parsed > forecast_end:
        return False
    return True


def build_forecast(
    location_data: dict,
    time_series_data: dict,
    weather_data: dict,
    forecast_start: date | None = None,
    forecast_end: date | None = None,
    astro_data: dict | None = None,
    *,
    seventimer_enabled: bool = True,
) -> ForecastResponse:
    """Combine IPGeolocation, Open-Meteo, and optional 7timer data into a forecast."""
    location_block = location_data.get("location", {})
    label = location_block.get("location_string") or location_block.get("city") or "Unknown location"
    latitude = float(location_block.get("latitude", 0))
    longitude = float(location_block.get("longitude", 0))
    timezone = weather_data.get("timezone", "UTC")

    astro_index: AstroIndex | None = None
    if seventimer_enabled and astro_data is not None:
        try:
            astro_index = build_astro_index(astro_data, timezone)
        except Exception:
            astro_index = None

    hourly_times: list[str] = weather_data.get("hourly", {}).get("time", [])
    hourly_weather = weather_data.get("hourly", {})
    minutely_weather = weather_data.get("minutely_15", {})
    daily_lookup = _build_daily_lookup(weather_data)
    score_step_minutes = _detect_score_step(weather_data)

    hourly_by_time = _index_weather_block(hourly_weather, HOURLY_WEATHER_FIELDS)
    minutely_by_time = _index_weather_block(minutely_weather, HOURLY_WEATHER_FIELDS)
    score_slots = _half_hour_slots_from_hourly_times(hourly_times)

    astronomy_days: list[dict] = time_series_data.get("astronomy", [])
    astronomy_by_date = {day.get("date", ""): day for day in astronomy_days if day.get("date")}
    moon_anchor = _moon_anchor_from_single_day(location_data)
    nights: list[NightForecast] = []

    prior_day_dark_window: TimeWindow | None = None
    if forecast_start is not None:
        prior_day = astronomy_by_date.get((forecast_start - timedelta(days=1)).isoformat())
        if prior_day:
            prior_day_dark_window = _dark_window_from_astronomy_day(prior_day)

    for day in astronomy_days:
        day_date = day.get("date", "")
        if not _in_forecast_window(day_date, forecast_start, forecast_end):
            continue

        night_begin = day.get("night_begin")
        night_end = day.get("night_end") or day.get("morning", {}).get("astronomical_twilight_end")

        moon_illumination = _resolve_moon_illumination(day, moon_anchor, day_date)
        moon_phase = day.get("moon_phase", "UNKNOWN")
        moonrise, moonset = _resolve_night_moon_times(day, astronomy_by_date)

        if not night_begin or not night_end:
            nights.append(
                NightForecast(
                    date=day_date,
                    rating="Poor",
                    score=None,
                    moon_phase=moon_phase,
                    moon_illumination=moon_illumination,
                    no_darkness=True,
                )
            )
            continue

        dark_window = TimeWindow(start=night_begin, end=night_end)
        night_meteor_showers = meteor_showers.meteor_highlights_for_night(
            latitude,
            longitude,
            timezone,
            day_date,
            night_begin,
            night_end,
        )
        hourly_scores: list[HourlyScore] = []
        night_slots = _darkness_slots_for_night(
            day_date,
            night_begin,
            night_end,
            score_slots,
        )

        for slot_dt in night_slots:
            wx = _weather_at_slot(slot_dt, minutely_by_time, hourly_by_time)
            if not any(wx.get(field) is not None for field in HOURLY_WEATHER_FIELDS):
                continue

            effective_moon, moon_up, moon_altitude = _effective_moon_illumination(
                slot_dt,
                moon_illumination,
                astronomy_by_date,
                latitude,
                longitude,
                timezone,
            )
            seeing, transparency = lookup_astro_at(slot_dt, astro_index)
            score = _hour_score(
                cloud_cover=wx.get("cloud_cover"),
                visibility=wx.get("visibility"),
                moon_illumination=effective_moon,
                precipitation=wx.get("precipitation"),
                weather_code=wx.get("weather_code"),
            )
            hourly_scores.append(
                HourlyScore(
                    time=slot_dt.strftime("%H:%M"),
                    at=slot_dt.isoformat(),
                    score=score,
                    moon_illumination_effective=effective_moon,
                    moon_up=moon_up,
                    moon_altitude=moon_altitude,
                    cloud_cover=wx.get("cloud_cover"),
                    cloud_cover_low=wx.get("cloud_cover_low"),
                    cloud_cover_mid=wx.get("cloud_cover_mid"),
                    cloud_cover_high=wx.get("cloud_cover_high"),
                    visibility=wx.get("visibility"),
                    seeing=seeing,
                    transparency=transparency,
                    precipitation=wx.get("precipitation"),
                    precipitation_probability=wx.get("precipitation_probability"),
                    dew_point=wx.get("dew_point_2m"),
                    temperature=wx.get("temperature_2m"),
                )
            )

        hourly_scores.sort(key=lambda entry: entry.at)
        cloud_summary, precip_summary = _summarize_hourly_weather(hourly_scores)
        daily_weather = daily_lookup.get(day_date, {})

        effective_values = [
            entry.moon_illumination_effective
            for entry in hourly_scores
            if entry.moon_illumination_effective is not None
        ]
        moon_sky_glow_avg = _average(effective_values)
        if moon_sky_glow_avg is not None:
            moon_sky_glow_avg = round(moon_sky_glow_avg, 1)

        if hourly_scores:
            avg_score = sum(h.score for h in hourly_scores) / len(hourly_scores)
            rating = _rating_from_score(avg_score)
            score = int(round(avg_score))
        else:
            rating = "Poor"
            score = 0

        astro_limited = not any(
            entry.seeing is not None or entry.transparency is not None
            for entry in hourly_scores
        )

        nights.append(
            NightForecast(
                date=day_date,
                rating=rating,
                score=score,
                moon_phase=moon_phase,
                moon_illumination=moon_illumination,
                moonrise=moonrise,
                moonset=moonset,
                moon_sky_glow_avg=moon_sky_glow_avg,
                temperature_high=daily_weather.get("temperature_high"),
                temperature_low=daily_weather.get("temperature_low"),
                cloud_cover=cloud_summary,
                precipitation=precip_summary,
                dark_window=dark_window,
                best_hours=_find_best_hours(hourly_scores),
                hourly=hourly_scores,
                meteor_showers=night_meteor_showers,
                astro_forecast_limited=astro_limited,
            )
        )

    return ForecastResponse(
        location=LocationInfo(
            label=label,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        ),
        nights=nights,
        score_step_minutes=score_step_minutes,
        prior_day_dark_window=prior_day_dark_window,
    )

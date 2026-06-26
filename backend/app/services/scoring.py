"""Merge astronomy darkness windows with hourly weather into stargazing scores."""

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


def _hour_score(
    cloud_cover: float | None,
    visibility: float | None,
    moon_illumination: float,
    precipitation: float | None,
    weather_code: float | None,
) -> int:
    cloud = cloud_cover if cloud_cover is not None else 100.0
    cloud_score = max(0.0, 100.0 - cloud)

    if visibility is None:
        visibility_score = 50.0
    else:
        visibility_score = min(visibility / 10000.0, 1.0) * 100.0

    moon_score = max(0.0, 100.0 - abs(moon_illumination))

    precip_penalty = 0.0
    if precipitation is not None and precipitation > 0:
        precip_penalty = min(precipitation * 20.0, 100.0)
    weather_score = _weather_penalty(weather_code)
    precip_score = max(0.0, weather_score - precip_penalty)

    total = (
        cloud_score * 0.40
        + visibility_score * 0.25
        + moon_score * 0.25
        + precip_score * 0.10
    )
    return int(round(max(0.0, min(100.0, total))))


def _time_to_minutes(time_str: str) -> int:
    hour, minute = _parse_time(time_str)
    return hour * 60 + minute


def _is_in_nights_darkness(
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
    begin_minutes = _time_to_minutes(night_begin)
    end_minutes = _time_to_minutes(night_end)
    hour_minutes = hour_dt.hour * 60 + hour_dt.minute
    hour_date = hour_dt.date()
    day = datetime.fromisoformat(day_date).date()
    next_day = day + timedelta(days=1)

    if begin_minutes <= end_minutes:
        return hour_date == day and begin_minutes <= hour_minutes < end_minutes

    if hour_date == day and hour_minutes >= begin_minutes:
        return True
    if hour_date == next_day and hour_minutes < end_minutes:
        return True
    return False


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


def build_forecast(
    location_data: dict,
    time_series_data: dict,
    weather_data: dict,
) -> ForecastResponse:
    """Combine IPGeolocation and Open-Meteo data into a 7-day stargazing forecast."""
    location_block = location_data.get("location", {})
    label = location_block.get("location_string") or location_block.get("city") or "Unknown location"
    latitude = float(location_block.get("latitude", 0))
    longitude = float(location_block.get("longitude", 0))
    timezone = weather_data.get("timezone", "UTC")

    hourly_times: list[str] = weather_data.get("hourly", {}).get("time", [])
    hourly_weather = weather_data.get("hourly", {})
    daily_lookup = _build_daily_lookup(weather_data)

    weather_by_time: dict[str, dict[str, float | None]] = {}
    for index, time_key in enumerate(hourly_times):
        weather_by_time[time_key] = {
            var: _value_at(hourly_weather, var, index)
            for var in HOURLY_WEATHER_FIELDS
        }

    astronomy_days: list[dict] = time_series_data.get("astronomy", [])
    moon_anchor = _moon_anchor_from_single_day(location_data)
    nights: list[NightForecast] = []

    for day in astronomy_days:
        day_date = day.get("date", "")
        night_begin = day.get("night_begin")
        night_end = day.get("night_end") or day.get("morning", {}).get("astronomical_twilight_end")

        moon_illumination = _resolve_moon_illumination(day, moon_anchor, day_date)
        moon_phase = day.get("moon_phase", "UNKNOWN")

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
        hourly_scores: list[HourlyScore] = []

        for time_key, wx in weather_by_time.items():
            try:
                hour_dt = datetime.fromisoformat(time_key)
            except ValueError:
                continue

            if not _is_in_nights_darkness(hour_dt, day_date, night_begin, night_end):
                continue

            score = _hour_score(
                cloud_cover=wx.get("cloud_cover"),
                visibility=wx.get("visibility"),
                moon_illumination=moon_illumination,
                precipitation=wx.get("precipitation"),
                weather_code=wx.get("weather_code"),
            )
            hourly_scores.append(
                HourlyScore(
                    time=hour_dt.strftime("%H:%M"),
                    at=hour_dt.isoformat(),
                    score=score,
                    cloud_cover=wx.get("cloud_cover"),
                    cloud_cover_low=wx.get("cloud_cover_low"),
                    cloud_cover_mid=wx.get("cloud_cover_mid"),
                    cloud_cover_high=wx.get("cloud_cover_high"),
                    visibility=wx.get("visibility"),
                    precipitation=wx.get("precipitation"),
                    precipitation_probability=wx.get("precipitation_probability"),
                    dew_point=wx.get("dew_point_2m"),
                    temperature=wx.get("temperature_2m"),
                )
            )

        hourly_scores.sort(key=lambda entry: entry.at)
        cloud_summary, precip_summary = _summarize_hourly_weather(hourly_scores)
        daily_weather = daily_lookup.get(day_date, {})

        if hourly_scores:
            avg_score = sum(h.score for h in hourly_scores) / len(hourly_scores)
            rating = _rating_from_score(avg_score)
            score = int(round(avg_score))
        else:
            rating = "Poor"
            score = 0

        nights.append(
            NightForecast(
                date=day_date,
                rating=rating,
                score=score,
                moon_phase=moon_phase,
                moon_illumination=moon_illumination,
                temperature_high=daily_weather.get("temperature_high"),
                temperature_low=daily_weather.get("temperature_low"),
                cloud_cover=cloud_summary,
                precipitation=precip_summary,
                dark_window=dark_window,
                best_hours=_find_best_hours(hourly_scores),
                hourly=hourly_scores,
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
    )

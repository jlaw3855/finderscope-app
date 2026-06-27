"""FreeAstroAPI moon phase client."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

import httpx

BASE_URL = "https://api.freeastroapi.com/api/v1/moon/phase"

SYNODIC_MONTH_DAYS = 29.53059
FULL_MOON_AGE_DAYS = SYNODIC_MONTH_DAYS / 2
FULL_MOON_AGE_TOLERANCE_DAYS = 1.0
FULL_MOON_MIN_ILLUMINATION_PCT = 98.0
FULL_MOON_PRACTICAL_ILLUMINATION_PCT = 99.5

SAMPLE_PROFILE_NOON = "noon"
SAMPLE_PROFILE_DARK = "dark"


class FreeAstroAPIError(Exception):
    """Raised when the FreeAstro API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


@dataclass(frozen=True)
class MoonPhaseResult:
    date: str
    phase_name: str
    illumination_pct: float
    age_days: float | None
    is_waxing: bool | None
    special_labels: list[str]
    svg: str | None


def theme_hash(moon_color: str, shadow_color: str) -> str:
    raw = f"{moon_color}|{shadow_color}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def local_noon_date_param(day: date) -> str:
    """Build FreeAstro ``date`` query value for local noon on a calendar day."""
    return f"{day.isoformat()}T12:00:00"


def moon_sample_date_param(day: date, sample_datetime: str | None = None) -> str:
    """Build FreeAstro ``date`` query value for a calendar day and optional local sample time."""
    if sample_datetime:
        return sample_datetime
    return local_noon_date_param(day)


def normalize_phase_display_name(
    phase_name: str,
    illumination_pct: float,
    age_days: float | None,
) -> str:
    """Map near-full gibbous phases to Full Moon for observer-friendly labels."""
    if phase_name == "Full Moon":
        return phase_name

    is_gibbous = "Gibbous" in phase_name
    if not is_gibbous:
        return phase_name

    if illumination_pct >= FULL_MOON_PRACTICAL_ILLUMINATION_PCT:
        return "Full Moon"

    if illumination_pct >= FULL_MOON_MIN_ILLUMINATION_PCT and age_days is not None:
        if abs(age_days - FULL_MOON_AGE_DAYS) <= FULL_MOON_AGE_TOLERANCE_DAYS:
            return "Full Moon"

    return phase_name


def parse_moon_phase_response(payload: dict, day: str) -> MoonPhaseResult:
    phase = payload.get("phase", {})
    special = payload.get("special_moon", {})
    visual = payload.get("moon_visual", {})

    illumination = phase.get("illumination")
    illumination_pct = round(float(illumination) * 100, 1) if illumination is not None else 0.0

    labels = special.get("labels") or []
    if not isinstance(labels, list):
        labels = []

    svg = visual.get("svg") if isinstance(visual, dict) else None

    raw_phase_name = str(phase.get("name", "Unknown"))
    age_days = float(phase["age_days"]) if phase.get("age_days") is not None else None
    phase_name = normalize_phase_display_name(raw_phase_name, illumination_pct, age_days)

    return MoonPhaseResult(
        date=day,
        phase_name=phase_name,
        illumination_pct=illumination_pct,
        age_days=age_days,
        is_waxing=phase.get("is_waxing") if isinstance(phase.get("is_waxing"), bool) else None,
        special_labels=[str(label) for label in labels],
        svg=str(svg) if svg else None,
    )


async def fetch_moon_phase(
    api_key: str,
    day: date,
    timezone_name: str,
    *,
    moon_color: str,
    shadow_color: str,
    include_visuals: bool = True,
    sample_datetime: str | None = None,
    sample_profile: str = SAMPLE_PROFILE_NOON,
) -> tuple[MoonPhaseResult, dict[str, str]]:
    """Fetch moon phase for a calendar date at local noon or an optional sample datetime."""
    sample_date = moon_sample_date_param(day, sample_datetime)
    params = {
        "date": sample_date,
        "tz_str": timezone_name,
        "include_visuals": str(include_visuals).lower(),
        "style_moon_color": moon_color,
        "style_shadow_color": shadow_color,
    }
    headers = {
        "x-api-key": api_key,
        "Idempotency-Key": (
            f"moon-{day.isoformat()}-{sample_profile}-{sample_date}-"
            f"{theme_hash(moon_color, shadow_color)}"
        ),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(BASE_URL, params=params, headers=headers)

    rate_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower().startswith("x-ratelimit-") or key.lower() == "retry-after"
    }

    if response.status_code == 429:
        retry_after_raw = response.headers.get("Retry-After")
        retry_after = float(retry_after_raw) if retry_after_raw else None
        raise FreeAstroAPIError(
            f"FreeAstro rate limit exceeded: {response.text}",
            status_code=429,
            retry_after=retry_after,
        )

    if response.status_code >= 400:
        raise FreeAstroAPIError(
            f"FreeAstro request failed: {response.text}",
            status_code=response.status_code,
        )

    payload = response.json()
    return parse_moon_phase_response(payload, day.isoformat()), rate_headers

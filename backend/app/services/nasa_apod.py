"""NASA Astronomy Picture of the Day (APOD) client."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.models.apod import ApodResponse
from app.services.http_client import get_http_client

BASE_URL = "https://api.nasa.gov/planetary/apod"

# * NASA publishes a new APOD at 04:00 UTC, not at midnight UTC.
APOD_RESET_HOUR_UTC = 4

_cache: dict[str, ApodResponse] = {}


class NasaApodError(Exception):
    """Raised when the NASA APOD API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _current_apod_day(*, now: datetime | None = None) -> date:
    """Return the APOD calendar date for the current moment."""
    current = now or datetime.now(UTC)
    return (current - timedelta(hours=APOD_RESET_HOUR_UTC)).date()


_SKY_SURPRISE_PATTERN = re.compile(r"\s*Sky Surprise:.*$", re.IGNORECASE | re.DOTALL)


def _strip_sky_surprise(explanation: str) -> str:
    """Remove APOD's promotional Sky Surprise footer (requires external link integration)."""
    return _SKY_SURPRISE_PATTERN.sub("", explanation).strip()


def _parse_apod_payload(payload: dict[str, Any]) -> ApodResponse:
    title = payload.get("title")
    day = payload.get("date")
    explanation = payload.get("explanation")
    media_type = payload.get("media_type")

    if not title or not day or not explanation or media_type not in {"image", "video"}:
        raise NasaApodError("NASA APOD response missing required fields.")

    copyright_raw = payload.get("copyright")
    copyright_value = str(copyright_raw).strip() if copyright_raw else None

    image_url: str | None = None
    video_url: str | None = None

    if media_type == "image":
        hdurl = payload.get("hdurl")
        url = payload.get("url")
        image_url = hdurl or url
        if not image_url:
            raise NasaApodError("NASA APOD image response missing url.")
    else:
        video_url = payload.get("url")
        if not video_url:
            raise NasaApodError("NASA APOD video response missing url.")

    return ApodResponse(
        title=str(title),
        date=str(day),
        explanation=_strip_sky_surprise(str(explanation)),
        media_type=media_type,
        image_url=image_url,
        video_url=video_url,
        copyright=copyright_value,
    )


async def fetch_apod(api_key: str, *, day: date | None = None) -> ApodResponse:
    """Fetch a single APOD entry from NASA for the given date."""
    target_day = day or _current_apod_day()
    params: dict[str, str] = {
        "api_key": api_key,
        "date": target_day.isoformat(),
    }

    response = await get_http_client().get(BASE_URL, params=params)
    if response.status_code >= 400:
        raise NasaApodError(
            f"NASA APOD request failed: {response.text}",
            status_code=response.status_code,
        )

    payload = response.json()
    if not isinstance(payload, dict):
        raise NasaApodError("NASA APOD response is not a JSON object.")

    return _parse_apod_payload(payload)


async def get_apod(api_key: str, *, day: date | None = None) -> ApodResponse:
    """Return APOD for the given date, using a simple in-memory daily cache."""
    target_day = day or _current_apod_day()
    cache_key = target_day.isoformat()

    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    apod = await fetch_apod(api_key, day=target_day)
    _cache[cache_key] = apod
    return apod


def clear_apod_cache() -> None:
    """Clear the in-memory APOD cache (for tests)."""
    _cache.clear()

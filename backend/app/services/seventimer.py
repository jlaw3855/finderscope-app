"""7timer ASTRO forecast client for seeing and atmospheric transparency."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.astronomy_time import cached_zoneinfo
from app.services.http_client import get_http_client

BASE_URL = "https://www.7timer.info/bin/api.pl"
MAX_LOOKUP_DELTA = timedelta(minutes=90)
INVALID_BIN = -9999


class SevenTimerError(Exception):
    """Raised when the 7timer API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class AstroBucket:
    """Single 3-hour 7timer astro forecast bucket in local time."""

    at_local: datetime
    seeing: int | None
    transparency: int | None


@dataclass(frozen=True)
class AstroIndex:
    """Time-indexed 7timer astro buckets for nearest-slot lookup."""

    init_utc: datetime
    valid_until_local: datetime
    buckets: tuple[AstroBucket, ...]


def parse_init_utc(init: str) -> datetime:
    """Parse 7timer model init string (YYYYMMDDHH) as UTC."""
    if len(init) != 10 or not init.isdigit():
        raise SevenTimerError(f"Invalid 7timer init timestamp: {init!r}")
    return datetime.strptime(init, "%Y%m%d%H").replace(tzinfo=UTC)


def _parse_bin(raw: object) -> int | None:
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if value == INVALID_BIN or value < 1 or value > 8:
        return None
    return value


def categorical_astro_score(value: int | None) -> float | None:
    """Map 7timer bin 1 (best) … 8 (worst) to a 0–100 sub-score."""
    if value is None:
        return None
    return (8 - value) / 7 * 100


async def fetch_astro_forecast(
    latitude: float,
    longitude: float,
    *,
    altitude_correction: int = 0,
) -> dict[str, Any]:
    """Fetch 72-hour ASTRO product JSON for coordinates."""
    params: dict[str, str | float | int] = {
        "lon": round(longitude, 3),
        "lat": round(latitude, 3),
        "product": "astro",
        "output": "json",
    }
    if altitude_correction in (0, 2, 7):
        params["ac"] = altitude_correction

    response = await get_http_client().get(BASE_URL, params=params)
    if response.status_code >= 400:
        raise SevenTimerError(
            f"7timer request failed: {response.text}",
            status_code=response.status_code,
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise SevenTimerError("7timer returned invalid or empty JSON.") from exc

    if not isinstance(payload, dict):
        raise SevenTimerError("7timer response is not a JSON object.")
    if payload.get("product") != "astro":
        raise SevenTimerError("7timer response is not an astro product.")
    if "init" not in payload or "dataseries" not in payload:
        raise SevenTimerError("7timer response missing init or dataseries.")

    return payload


def build_astro_index(payload: dict[str, Any], timezone_name: str) -> AstroIndex:
    """Build local-time astro buckets from a 7timer ASTRO payload."""
    init_utc = parse_init_utc(str(payload["init"]))
    tz = cached_zoneinfo(timezone_name)
    buckets: list[AstroBucket] = []
    max_timepoint = 0

    for entry in payload.get("dataseries", []):
        timepoint = entry.get("timepoint")
        if timepoint is None:
            continue
        try:
            hours = int(timepoint)
        except (TypeError, ValueError):
            continue
        max_timepoint = max(max_timepoint, hours)

        at_utc = init_utc + timedelta(hours=hours)
        at_local = at_utc.astimezone(tz).replace(tzinfo=None)
        buckets.append(
            AstroBucket(
                at_local=at_local,
                seeing=_parse_bin(entry.get("seeing")),
                transparency=_parse_bin(entry.get("transparency")),
            )
        )

    buckets.sort(key=lambda bucket: bucket.at_local)
    valid_until_utc = init_utc + timedelta(hours=max_timepoint)
    valid_until_local = valid_until_utc.astimezone(tz).replace(tzinfo=None)

    return AstroIndex(
        init_utc=init_utc,
        valid_until_local=valid_until_local,
        buckets=tuple(buckets),
    )


def lookup_astro_at(slot_dt: datetime, index: AstroIndex | None) -> tuple[int | None, int | None]:
    """Return nearest seeing/transparency bins for a local score slot."""
    if index is None or not index.buckets:
        return None, None

    if slot_dt >= index.valid_until_local:
        return None, None

    nearest: AstroBucket | None = None
    nearest_delta = MAX_LOOKUP_DELTA + timedelta(seconds=1)

    for bucket in index.buckets:
        delta = abs(bucket.at_local - slot_dt)
        if delta < nearest_delta:
            nearest = bucket
            nearest_delta = delta

    if nearest is None or nearest_delta > MAX_LOOKUP_DELTA:
        return None, None

    return nearest.seeing, nearest.transparency

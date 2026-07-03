"""Site sky darkness lookup via lightpollutionmap.info."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Literal

import httpx

from app.models.dso_visibility import SiteSkyConditions

logger = logging.getLogger(__name__)

QUERY_RASTER_URL = "https://www.lightpollutionmap.info/QueryRaster/"
SKY_BRIGHTNESS_LAYER = "wa_2015"
NATURAL_BACKGROUND_MCD_M2 = 0.171168465
MCD_M2_TO_TOTAL_DIVISOR = 108_000_000.0

# * Standard SQM (mag/arcsec²) to Bortle class thresholds.
SQM_BORTLE_THRESHOLDS: tuple[tuple[float, int], ...] = (
    (21.75, 1),
    (21.50, 2),
    (21.25, 3),
    (21.00, 4),
    (20.50, 5),
    (20.00, 6),
    (19.50, 7),
    (18.50, 8),
)

FALLBACK_SITE = SiteSkyConditions(
    bortle=5,
    sqm=20.5,
    limiting_magnitude=5.6,
    source="fallback",
)

_CACHE: dict[str, tuple[float, SiteSkyConditions]] = {}
_CACHE_TTL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class _CacheKey:
    lat: float
    lon: float


def _cache_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.3f},{longitude:.3f}"


def sqm_to_bortle(sqm: float) -> int:
    """Map zenith SQM to Bortle scale (1 = darkest, 9 = brightest)."""
    for threshold, bortle in SQM_BORTLE_THRESHOLDS:
        if sqm >= threshold:
            return bortle
    return 9


def sqm_to_nelm(sqm: float) -> float:
    """Estimate naked-eye limiting magnitude from SQM using Unihedron formula."""
    return round(7.93 - 5.0 * math.log10(math.pow(10, 4.316 - sqm / 5.0) + 1.0), 2)


def artificial_brightness_to_sqm(artificial_brightness_mcd_m2: float) -> float:
    """Convert World Atlas artificial brightness to zenith SQM."""
    total = artificial_brightness_mcd_m2 + NATURAL_BACKGROUND_MCD_M2
    return round(math.log10(total / MCD_M2_TO_TOTAL_DIVISOR) / -0.4, 2)


def parse_query_raster_response(body: str) -> float:
    """Parse lightpollutionmap QueryRaster response to artificial brightness."""
    payload = body.strip().split(",", maxsplit=1)[0]
    values = [part.strip() for part in payload.split(";") if part.strip()]
    if not values:
        raise ValueError("Empty QueryRaster response")
    return float(values[-1])


async def _fetch_artificial_brightness(
    latitude: float,
    longitude: float,
    *,
    client: httpx.AsyncClient | None = None,
) -> float:
    params = {
        "ql": SKY_BRIGHTNESS_LAYER,
        "qt": "point_t",
        "qd": f"{latitude},{longitude}",
    }
    if client is None:
        async with httpx.AsyncClient(timeout=15.0) as owned:
            response = await owned.get(QUERY_RASTER_URL, params=params)
    else:
        response = await client.get(QUERY_RASTER_URL, params=params)
    response.raise_for_status()
    return parse_query_raster_response(response.text)


def _build_site_conditions(artificial_brightness: float) -> SiteSkyConditions:
    sqm = artificial_brightness_to_sqm(artificial_brightness)
    return SiteSkyConditions(
        bortle=sqm_to_bortle(sqm),
        sqm=sqm,
        limiting_magnitude=sqm_to_nelm(sqm),
        source="lightpollutionmap",
    )


async def lookup_site_darkness(
    latitude: float,
    longitude: float,
    *,
    client: httpx.AsyncClient | None = None,
) -> SiteSkyConditions:
    """Return site Bortle/SQM/NELM for coordinates, with cache and fallback."""
    key = _cache_key(latitude, longitude)
    cached = _CACHE.get(key)
    now = time.monotonic()
    if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        artificial = await _fetch_artificial_brightness(latitude, longitude, client=client)
        site = _build_site_conditions(artificial)
    except (httpx.HTTPError, ValueError, TypeError, OSError) as exc:
        logger.warning("Light pollution lookup failed for %s: %s", key, exc)
        site = FALLBACK_SITE

    _CACHE[key] = (now, site)
    return site

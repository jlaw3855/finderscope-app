"""Rate-limited queue for FreeAstro moon enrichment requests."""

from __future__ import annotations

import asyncio
import time
from datetime import date

from app.config import Settings
from app.services import freeastroapi, moon_cache

MIN_REQUEST_INTERVAL_SECONDS = 1.0

_queue_lock = asyncio.Lock()
_last_request_at = 0.0
_inflight: dict[str, asyncio.Task] = {}


async def _throttle() -> None:
    global _last_request_at
    async with _queue_lock:
        now = time.monotonic()
        elapsed = now - _last_request_at
        if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
            await asyncio.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)
        _last_request_at = time.monotonic()


async def fetch_and_cache_date(
    settings: Settings,
    day: date,
    timezone_name: str,
    *,
    sample_datetime: str | None = None,
    sample_profile: str = freeastroapi.SAMPLE_PROFILE_NOON,
) -> moon_cache.CachedMoonEntry | None:
    """Fetch one date through the rate-limited queue and store in cache."""
    if not settings.moon_enrichment_enabled or not settings.freeastro_api_key:
        return None

    theme_key = freeastroapi.theme_hash(
        settings.moon_visual_moon_color,
        settings.moon_visual_shadow_color,
    )
    date_str = day.isoformat()
    key = moon_cache.cache_key(date_str, theme_key, sample_profile)

    existing = moon_cache.get_cached(date_str, theme_key, sample_profile)
    if existing is not None:
        return existing

    if key in _inflight:
        return await _inflight[key]

    task = asyncio.create_task(
        _fetch_one(
            settings,
            day,
            timezone_name,
            theme_key,
            sample_datetime=sample_datetime,
            sample_profile=sample_profile,
        )
    )
    _inflight[key] = task
    try:
        return await task
    finally:
        _inflight.pop(key, None)


async def _fetch_one(
    settings: Settings,
    day: date,
    timezone_name: str,
    theme_key: str,
    *,
    sample_datetime: str | None = None,
    sample_profile: str = freeastroapi.SAMPLE_PROFILE_NOON,
) -> moon_cache.CachedMoonEntry | None:
    if not moon_cache.quota_available():
        return None

    await _throttle()

    try:
        result, headers = await freeastroapi.fetch_moon_phase(
            settings.freeastro_api_key,
            day,
            timezone_name,
            moon_color=settings.moon_visual_moon_color,
            shadow_color=settings.moon_visual_shadow_color,
            sample_datetime=sample_datetime,
            sample_profile=sample_profile,
        )
    except freeastroapi.FreeAstroAPIError:
        return None

    moon_cache.update_quota_from_headers(headers, increment=True)
    return moon_cache.store_cached(
        date=result.date,
        theme_key=theme_key,
        phase_name=result.phase_name,
        illumination_pct=result.illumination_pct,
        age_days=result.age_days,
        is_waxing=result.is_waxing,
        special_labels=result.special_labels,
        svg=result.svg,
        sample_profile=sample_profile,
    )


async def prefetch_dates(
    settings: Settings,
    dates: list[date],
    timezone_name: str,
) -> list[moon_cache.CachedMoonEntry]:
    """Fetch missing dates sequentially at 1 RPS."""
    results: list[moon_cache.CachedMoonEntry] = []
    for day in dates:
        cached = await fetch_and_cache_date(settings, day, timezone_name)
        if cached is not None:
            results.append(cached)
    return results

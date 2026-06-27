"""Orchestration for moon enrichment lookups and background backfill."""

from __future__ import annotations

import asyncio
from datetime import date

from app.config import Settings
from app.models.moon_enrichment import MoonEnrichmentEntry, MoonEnrichmentResponse
from app.services import freeastroapi, moon_cache, moon_enrichment_queue


def _theme_key(settings: Settings) -> str:
    return freeastroapi.theme_hash(
        settings.moon_visual_moon_color,
        settings.moon_visual_shadow_color,
    )


def _entry_from_cache(
    cached: moon_cache.CachedMoonEntry,
    sample_profile: str,
) -> MoonEnrichmentEntry:
    visual_url = (
        f"/api/moon/visual/{cached.date}.svg?profile={sample_profile}"
        if cached.svg_path
        else None
    )
    return MoonEnrichmentEntry(
        date=cached.date,
        phase_name=cached.phase_name,
        illumination_pct=cached.illumination_pct,
        age_days=cached.age_days,
        is_waxing=cached.is_waxing,
        special_labels=cached.special_labels,
        visual_url=visual_url,
    )


def _resolve_sample_profile(sample_times: dict[str, str] | None) -> str:
    if sample_times:
        return freeastroapi.SAMPLE_PROFILE_DARK
    return freeastroapi.SAMPLE_PROFILE_NOON


def _schedule_backfill(
    settings: Settings,
    missing: list[tuple[str, str | None]],
    timezone_name: str,
    sample_profile: str,
) -> None:
    if not missing:
        return

    async def _run() -> None:
        for date_str, sample_datetime in missing:
            await moon_enrichment_queue.fetch_and_cache_date(
                settings,
                date.fromisoformat(date_str),
                timezone_name,
                sample_datetime=sample_datetime,
                sample_profile=sample_profile,
            )

    asyncio.create_task(_run())


async def get_moon_enrichment(
    settings: Settings,
    dates: list[str],
    timezone_name: str,
    sample_times: dict[str, str] | None = None,
) -> MoonEnrichmentResponse:
    if not settings.moon_enrichment_enabled or not settings.freeastro_api_key:
        return MoonEnrichmentResponse(
            entries=[],
            status="unavailable",
            cached_count=0,
            pending_dates=dates,
        )

    if not moon_cache.quota_available():
        return MoonEnrichmentResponse(
            entries=[],
            status="unavailable",
            cached_count=0,
            pending_dates=dates,
        )

    theme_key = _theme_key(settings)
    sample_profile = _resolve_sample_profile(sample_times)
    entries: list[MoonEnrichmentEntry] = []
    missing: list[tuple[str, str | None]] = []

    for date_str in dates:
        cached = moon_cache.get_cached(date_str, theme_key, sample_profile)
        if cached is not None:
            entries.append(_entry_from_cache(cached, sample_profile))
        else:
            sample_datetime = (sample_times or {}).get(date_str)
            missing.append((date_str, sample_datetime))

    if missing:
        _schedule_backfill(settings, missing, timezone_name, sample_profile)

    missing_dates = [date_str for date_str, _ in missing]
    if not entries and missing_dates:
        status = "pending"
    elif missing_dates:
        status = "partial"
    else:
        status = "complete"

    return MoonEnrichmentResponse(
        entries=entries,
        status=status,
        cached_count=len(entries),
        pending_dates=missing_dates,
    )

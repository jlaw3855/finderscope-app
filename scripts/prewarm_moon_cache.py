#!/usr/bin/env python3
"""Prewarm FreeAstro moon cache for the next seven calendar dates."""

from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings
from app.services import freeastroapi, moon_cache, moon_enrichment_queue


async def main() -> int:
    settings = Settings()
    if not settings.freeastro_api_key:
        print("FREEASTRO_API_KEY not set; skipping moon cache prewarm.")
        return 0

    if not settings.moon_enrichment_enabled:
        print("Moon enrichment disabled; skipping prewarm.")
        return 0

    theme_key = freeastroapi.theme_hash(
        settings.moon_visual_moon_color,
        settings.moon_visual_shadow_color,
    )
    today = date.today()
    dates = [today + timedelta(days=offset) for offset in range(7)]

    missing = [
        day
        for day in dates
        if moon_cache.get_cached(day.isoformat(), theme_key) is None
    ]

    if not missing:
        print("Moon cache already warm for the next 7 dates.")
        return 0

    print(f"Prewarming {len(missing)} moon cache entries at 1 req/sec...")
    await moon_enrichment_queue.prefetch_dates(settings, missing, "UTC")
    print("Moon cache prewarm complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

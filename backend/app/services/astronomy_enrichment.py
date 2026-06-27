"""Enrich astronomy events with NoctuaSky catalog metadata."""

from __future__ import annotations

import asyncio
import re

from app.config import Settings
from app.models.astronomy import AstronomyEvent, SkySourceEnrichment
from app.services import noctua

PLANET_NAMES = (
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Moon",
    "Sun",
)


def skysource_keys_for_event(event: AstronomyEvent) -> list[str]:
    """Return Noctua lookup keys for an event, in priority order."""
    if event.category == "lunar_eclipse":
        return ["Moon"]
    if event.category == "solar_eclipse":
        return ["Sun"]
    if event.category == "transit":
        for name in ("Mercury", "Venus"):
            if name in event.title:
                return [name]
        return []
    if event.category == "opposition":
        for name in ("Neptune", "Uranus", "Saturn", "Jupiter", "Mars"):
            if name in event.title:
                return [name]
        return []
    if event.category == "conjunction":
        if " and " in event.title:
            parts = event.title.replace(" conjunction", "").split(" and ")
            return [part.strip() for part in parts if part.strip()]
        for name in ("Mercury", "Venus"):
            if name in event.title:
                return [name]
        return []
    if event.category == "meteor_shower":
        match = re.search(r"\(([^)]+)\)", event.title)
        if match:
            return [match.group(1).strip()]
        return []
    return []


def _payload_to_enrichment(query: str, payload: dict) -> SkySourceEnrichment:
    return SkySourceEnrichment(
        query=query,
        short_name=payload.get("short_name"),
        types=list(payload.get("types") or []),
        interest=payload.get("interest"),
        names=list(payload.get("names") or []),
        model=payload.get("model"),
    )


async def _fetch_one(settings: Settings, key: str) -> tuple[str, dict | None]:
    payload = await noctua.fetch_skysource_by_name(settings, key)
    if payload is not None:
        return key, payload
    results = await noctua.search_skysources(settings, key, limit=1)
    if results:
        return key, results[0]
    return key, None


async def enrich_astronomy_events(
    events: list[AstronomyEvent],
    settings: Settings,
) -> list[AstronomyEvent]:
    """Attach Noctua skysource metadata to each event; fail-open on errors."""
    if not settings.noctua_enrichment_enabled or not events:
        return events

    keys: list[str] = []
    for event in events:
        keys.extend(skysource_keys_for_event(event))
    unique_keys = list(dict.fromkeys(keys))
    if not unique_keys:
        return events

    semaphore = asyncio.Semaphore(5)

    async def bounded_fetch(key: str) -> tuple[str, dict | None]:
        async with semaphore:
            return await _fetch_one(settings, key)

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*(bounded_fetch(key) for key in unique_keys)),
            timeout=settings.noctua_enrichment_budget_seconds,
        )
    except TimeoutError:
        return events

    lookup = {key: payload for key, payload in results if payload is not None}
    enriched: list[AstronomyEvent] = []
    for event in events:
        subjects: list[SkySourceEnrichment] = []
        for key in skysource_keys_for_event(event):
            payload = lookup.get(key)
            if payload is not None:
                subjects.append(_payload_to_enrichment(key, payload))
        enriched.append(event.model_copy(update={"subjects": subjects}))
    return enriched

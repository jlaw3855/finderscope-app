"""Astronomy summary routes."""

import asyncio

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.astronomy import AstronomyRequest, AstronomyResponse
from app.services.astronomy_enrichment import enrich_astronomy_events
from app.services.astronomy_events import search_astronomy_events
from app.services.celestial_almanac import compute_celestial_almanac
from app.services.planet_visibility import compute_planet_visibility

router = APIRouter(prefix="/api", tags=["astronomy"])


@router.post("/astronomy", response_model=AstronomyResponse)
async def get_astronomy_summary(
    request: AstronomyRequest,
    settings: Settings = Depends(get_settings),
) -> AstronomyResponse:
    events_task = asyncio.create_task(
        asyncio.to_thread(search_astronomy_events, request.latitude, request.longitude)
    )
    planet_task = asyncio.create_task(
        asyncio.to_thread(
            compute_planet_visibility,
            request.latitude,
            request.longitude,
            request.timezone,
            request.dates,
        )
    )
    almanac_task = asyncio.create_task(
        asyncio.to_thread(
            compute_celestial_almanac,
            request.latitude,
            request.longitude,
            request.timezone,
            request.dates,
        )
    )
    events = await events_task
    events = await enrich_astronomy_events(events, settings)
    planet_visibility = await planet_task
    almanac = await almanac_task
    return AstronomyResponse(
        events=events,
        planet_visibility=planet_visibility,
        almanac=almanac,
    )

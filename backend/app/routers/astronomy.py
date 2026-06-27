"""Astronomy summary routes."""

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.astronomy import AstronomyRequest, AstronomyResponse
from app.services.astronomy_enrichment import enrich_astronomy_events
from app.services.astronomy_events import search_astronomy_events
from app.services.planet_visibility import compute_planet_visibility

router = APIRouter(prefix="/api", tags=["astronomy"])


@router.post("/astronomy", response_model=AstronomyResponse)
async def get_astronomy_summary(
    request: AstronomyRequest,
    settings: Settings = Depends(get_settings),
) -> AstronomyResponse:
    events = search_astronomy_events(request.latitude, request.longitude)
    events = await enrich_astronomy_events(events, settings)
    planet_visibility = compute_planet_visibility(
        request.latitude,
        request.longitude,
        request.timezone,
        request.dates,
    )
    return AstronomyResponse(events=events, planet_visibility=planet_visibility)

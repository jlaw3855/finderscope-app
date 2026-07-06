"""DSO visibility API routes."""

import asyncio

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.dso_visibility import DsoVisibilityRequest, DsoVisibilityResponse
from app.services.dso_visibility import compute_dso_visibility
from app.services.http_client import get_http_client
from app.services.light_pollution import lookup_site_darkness

router = APIRouter(prefix="/api", tags=["dso"])


@router.post("/dso-visibility", response_model=DsoVisibilityResponse)
async def get_dso_visibility(
    request: DsoVisibilityRequest,
    _settings: Settings = Depends(get_settings),
) -> DsoVisibilityResponse:
    client = get_http_client()
    site = await lookup_site_darkness(
        request.latitude,
        request.longitude,
        client=client,
    )
    dso_visibility = await asyncio.to_thread(
        compute_dso_visibility,
        request.latitude,
        request.longitude,
        request.timezone,
        request.dates,
        site,
    )
    return DsoVisibilityResponse(site_sky=site, dso_visibility=dso_visibility)

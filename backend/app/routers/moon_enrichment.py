"""Moon enrichment endpoints backed by FreeAstroAPI cache."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.config import Settings, get_settings
from app.models.moon_enrichment import MoonEnrichmentResponse
from app.services import freeastroapi, moon_cache, moon_enrichment

router = APIRouter(prefix="/api/moon", tags=["moon"])


@router.get("/enrichment", response_model=MoonEnrichmentResponse)
async def get_moon_enrichment(
    dates: str = Query(..., description="Comma-separated YYYY-MM-DD dates"),
    timezone: str = Query("UTC", description="IANA timezone for local phase sampling"),
    sample_times: str | None = Query(
        None,
        description=(
            "Optional comma-separated local sample datetimes (YYYY-MM-DDTHH:MM:SS), "
            "parallel to dates; uses astronomical darkness midpoint when provided"
        ),
    ),
    settings: Settings = Depends(get_settings),
) -> MoonEnrichmentResponse:
    date_list = [part.strip() for part in dates.split(",") if part.strip()]
    if not date_list:
        raise HTTPException(status_code=422, detail="At least one date is required.")

    for date_str in date_list:
        try:
            date.fromisoformat(date_str)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid date format: {date_str}",
            ) from exc

    sample_times_by_date: dict[str, str] | None = None
    if sample_times is not None:
        sample_list = [part.strip() for part in sample_times.split(",") if part.strip()]
        if len(sample_list) != len(date_list):
            raise HTTPException(
                status_code=422,
                detail="sample_times must have the same number of entries as dates.",
            )
        sample_times_by_date = dict(zip(date_list, sample_list, strict=True))

    return await moon_enrichment.get_moon_enrichment(
        settings,
        date_list,
        timezone,
        sample_times_by_date,
    )


@router.get("/visual/{day}.svg")
async def get_moon_visual(
    day: str,
    profile: str = Query(
        freeastroapi.SAMPLE_PROFILE_DARK,
        description="Cache profile: dark (night midpoint) or noon",
    ),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        date.fromisoformat(day)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid date format.") from exc

    if profile not in {freeastroapi.SAMPLE_PROFILE_DARK, freeastroapi.SAMPLE_PROFILE_NOON}:
        raise HTTPException(status_code=422, detail="Invalid profile.")

    theme_key = freeastroapi.theme_hash(
        settings.moon_visual_moon_color,
        settings.moon_visual_shadow_color,
    )
    svg = moon_cache.read_svg(day, theme_key, profile)
    if svg is None:
        raise HTTPException(status_code=404, detail="Moon visual not cached for this date.")

    return Response(content=svg, media_type="image/svg+xml")

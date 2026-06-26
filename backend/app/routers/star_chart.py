"""Star chart endpoint proxying AstronomyAPI."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.star_chart import StarChartRequest, StarChartResponse
from app.services import astronomyapi

router = APIRouter(prefix="/api", tags=["star-chart"])


@router.post("/star-chart", response_model=StarChartResponse)
async def create_star_chart(
    body: StarChartRequest,
    settings: Settings = Depends(get_settings),
) -> StarChartResponse:
    try:
        image_url, view_type = await astronomyapi.generate_star_chart(settings, body)
        return StarChartResponse(image_url=image_url, view_type=view_type)
    except astronomyapi.AstronomyAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=str(exc),
        ) from exc

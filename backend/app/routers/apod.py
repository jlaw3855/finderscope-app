"""NASA APOD proxy endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.models.apod import ApodResponse
from app.services.nasa_apod import NasaApodError, get_apod

router = APIRouter(prefix="/api/apod", tags=["apod"])


@router.get("", response_model=ApodResponse)
async def read_apod(
    day: str | None = Query(
        None,
        alias="date",
        description="Optional YYYY-MM-DD date (defaults to current APOD day; resets at 04:00 UTC)",
    ),
    settings: Settings = Depends(get_settings),
) -> ApodResponse:
    parsed_day: date | None = None
    if day is not None:
        try:
            parsed_day = date.fromisoformat(day)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid date format.") from exc

    try:
        return await get_apod(settings.nasa_api_key, day=parsed_day)
    except NasaApodError as exc:
        status_code = exc.status_code if exc.status_code and exc.status_code < 500 else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

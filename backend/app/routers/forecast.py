"""Forecast endpoint orchestrating IPGeolocation, Open-Meteo, and scoring."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.forecast import ForecastRequest, ForecastResponse
from app.services import ipgeolocation, openmeteo, scoring

router = APIRouter(prefix="/api", tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(
    body: ForecastRequest,
    settings: Settings = Depends(get_settings),
) -> ForecastResponse:
    try:
        location_data = await ipgeolocation.resolve_location(settings, body.address.strip())
        latitude = float(location_data["location"]["latitude"])
        longitude = float(location_data["location"]["longitude"])

        date_start, date_end = ipgeolocation.default_date_range()
        time_series_data = await ipgeolocation.fetch_time_series(
            settings, latitude, longitude, date_start, date_end
        )
        weather_data = await openmeteo.fetch_forecast(latitude, longitude)

        return scoring.build_forecast(location_data, time_series_data, weather_data)
    except ipgeolocation.IPGeolocationError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=str(exc),
        ) from exc
    except openmeteo.OpenMeteoError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=str(exc),
        ) from exc

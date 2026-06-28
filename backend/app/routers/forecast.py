"""Forecast endpoint orchestrating IPGeolocation, Open-Meteo, and scoring."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.forecast import ForecastRequest, ForecastResponse
from app.services import forecast_cache, ipgeolocation, openmeteo, scoring

router = APIRouter(prefix="/api", tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(
    body: ForecastRequest,
    settings: Settings = Depends(get_settings),
) -> ForecastResponse:
    try:
        address = body.address.strip()
        location_data = None

        if settings.forecast_cache_enabled:
            geocode_key = forecast_cache.geocode_cache_key(address)
            location_data = forecast_cache.get_cached_entry(geocode_key)

        if location_data is None:
            location_data = await ipgeolocation.resolve_location(settings, address)
            if settings.forecast_cache_enabled:
                forecast_cache.store_cached_entry(
                    forecast_cache.geocode_cache_key(address),
                    forecast_cache.LAYER_GEOCODE,
                    location_data,
                    ttl_hours=settings.forecast_geocode_ttl_hours,
                )

        latitude = float(location_data["location"]["latitude"])
        longitude = float(location_data["location"]["longitude"])

        date_start, date_end = ipgeolocation.default_date_range()
        time_series_start, time_series_end = ipgeolocation.time_series_date_range()
        forecast_days = ipgeolocation.weather_forecast_days(date_start, date_end)

        time_series_data = None
        weather_data = None

        if settings.forecast_cache_enabled:
            ts_key = forecast_cache.astronomy_cache_key(
                latitude,
                longitude,
                time_series_start.isoformat(),
                time_series_end.isoformat(),
            )
            time_series_data = forecast_cache.get_cached_entry(ts_key)
            weather_key = forecast_cache.weather_cache_key(
                latitude,
                longitude,
                date_start.isoformat(),
                forecast_days,
            )
            weather_data = forecast_cache.get_cached_entry(weather_key)

        if time_series_data is None and weather_data is None:
            time_series_data, weather_data = await asyncio.gather(
                ipgeolocation.fetch_time_series(
                    settings, latitude, longitude, time_series_start, time_series_end
                ),
                openmeteo.fetch_forecast(
                    latitude,
                    longitude,
                    forecast_days=forecast_days,
                ),
            )
        elif time_series_data is None:
            time_series_data = await ipgeolocation.fetch_time_series(
                settings, latitude, longitude, time_series_start, time_series_end
            )
        elif weather_data is None:
            weather_data = await openmeteo.fetch_forecast(
                latitude,
                longitude,
                forecast_days=forecast_days,
            )

        if settings.forecast_cache_enabled:
            if time_series_data is not None:
                forecast_cache.store_cached_entry(
                    forecast_cache.astronomy_cache_key(
                        latitude,
                        longitude,
                        time_series_start.isoformat(),
                        time_series_end.isoformat(),
                    ),
                    forecast_cache.LAYER_ASTRONOMY,
                    time_series_data,
                    ttl_hours=settings.forecast_astronomy_ttl_hours,
                )
            if weather_data is not None:
                forecast_cache.store_cached_entry(
                    forecast_cache.weather_cache_key(
                        latitude,
                        longitude,
                        date_start.isoformat(),
                        forecast_days,
                    ),
                    forecast_cache.LAYER_WEATHER,
                    weather_data,
                    ttl_hours=settings.forecast_weather_ttl_hours,
                )

        return await asyncio.to_thread(
            scoring.build_forecast,
            location_data,
            time_series_data,
            weather_data,
            forecast_start=date_start,
            forecast_end=date_end,
        )
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

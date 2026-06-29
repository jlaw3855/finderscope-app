"""Forecast endpoint orchestrating IPGeolocation, Open-Meteo, 7timer, and scoring."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.forecast import ForecastRequest, ForecastResponse
from app.services import forecast_cache, ipgeolocation, openmeteo, scoring, seventimer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["forecast"])


async def _fetch_astro_if_enabled(
    settings: Settings,
    latitude: float,
    longitude: float,
) -> tuple[dict | None, bool]:
    if not settings.seventimer_enabled:
        return None, False
    try:
        payload = await seventimer.fetch_astro_forecast(
            latitude,
            longitude,
            altitude_correction=settings.seventimer_altitude_correction,
        )
        return payload, False
    except seventimer.SevenTimerError as exc:
        logger.warning("7timer astro fetch failed (fail-open): %s", exc)
        return None, True
    except Exception as exc:
        logger.warning("7timer astro fetch failed unexpectedly (fail-open): %s", exc)
        return None, True


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
        astro_data = None
        astro_data_unavailable = False

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
            astro_data = forecast_cache.get_cached_entry(
                forecast_cache.astro_cache_key(latitude, longitude)
            )

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

        if astro_data is None:
            astro_data, astro_data_unavailable = await _fetch_astro_if_enabled(
                settings,
                latitude,
                longitude,
            )

        forecast = await asyncio.to_thread(
            scoring.build_forecast,
            location_data,
            time_series_data,
            weather_data,
            forecast_start=date_start,
            forecast_end=date_end,
            astro_data=astro_data,
            seventimer_enabled=settings.seventimer_enabled,
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
            if astro_data is not None:
                forecast_cache.store_cached_entry(
                    forecast_cache.astro_cache_key(latitude, longitude),
                    forecast_cache.LAYER_ASTRO,
                    astro_data,
                    ttl_hours=settings.forecast_astro_ttl_hours,
                )

        if astro_data_unavailable:
            return forecast.model_copy(update={"astro_data_unavailable": True})

        return forecast
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

"""IPGeolocation.io Astronomy API client."""

from datetime import date, timedelta

import httpx

from app.config import Settings

BASE_URL = "https://api.ipgeolocation.io/v3/astronomy"


class IPGeolocationError(Exception):
    """Raised when the IPGeolocation API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


async def resolve_location(settings: Settings, address: str) -> dict:
    """Geocode an address and return astronomy data for the current day."""
    params = {
        "apiKey": settings.ipgeolocation_api_key,
        "location": address,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(BASE_URL, params=params)

    if response.status_code == 401:
        raise IPGeolocationError("Invalid IPGeolocation API key.", status_code=401)
    if response.status_code == 404:
        raise IPGeolocationError("Address not found. Try a more specific location.", status_code=404)
    if response.status_code >= 400:
        raise IPGeolocationError(
            f"IPGeolocation request failed: {response.text}",
            status_code=response.status_code,
        )

    return response.json()


async def fetch_time_series(
    settings: Settings,
    latitude: float,
    longitude: float,
    start: date,
    end: date,
) -> dict:
    """Fetch multi-day sun/moon/twilight data for coordinates."""
    params = {
        "apiKey": settings.ipgeolocation_api_key,
        "lat": latitude,
        "long": longitude,
        "dateStart": start.isoformat(),
        "dateEnd": end.isoformat(),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/timeSeries", params=params)

    if response.status_code >= 400:
        raise IPGeolocationError(
            f"IPGeolocation time series request failed: {response.text}",
            status_code=response.status_code,
        )

    return response.json()


def default_date_range() -> tuple[date, date]:
    today = date.today()
    return today, today + timedelta(days=6)


def time_series_date_range() -> tuple[date, date]:
    """Forecast window plus one prior day for pre-dawn darkness on the first night."""
    start, end = default_date_range()
    return start - timedelta(days=1), end


def weather_forecast_days(start: date, end: date) -> int:
    """Open-Meteo days needed to cover each night's pre-dawn hours on the following day."""
    return (end - start).days + 2

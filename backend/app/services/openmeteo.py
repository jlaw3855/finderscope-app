"""Open-Meteo forecast API client."""

import httpx

BASE_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARIABLES = [
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation",
    "precipitation_probability",
    "weather_code",
    "temperature_2m",
    "dew_point_2m",
]

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]


class OpenMeteoError(Exception):
    """Raised when the Open-Meteo API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


async def fetch_forecast(latitude: float, longitude: float, forecast_days: int = 7) -> dict:
    """Fetch hourly and daily weather forecast for stargazing conditions."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_VARIABLES),
        "daily": ",".join(DAILY_VARIABLES),
        "forecast_days": forecast_days,
        "timezone": "auto",
        "temperature_unit": "fahrenheit",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(BASE_URL, params=params)

    if response.status_code >= 400:
        raise OpenMeteoError(
            f"Open-Meteo request failed: {response.text}",
            status_code=response.status_code,
        )

    return response.json()

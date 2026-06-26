"""AstronomyAPI.com star chart and body positions client."""

import base64

import httpx

from app.config import Settings
from app.models.star_chart import StarChartRequest

STAR_CHART_URL = "https://api.astronomyapi.com/api/v2/studio/star-chart"
POSITIONS_URL = "https://api.astronomyapi.com/api/v2/bodies/positions"

# * Bodies within this many degrees of the horizon count as "near zenith".
NEAR_ZENITH_ALTITUDE_DEG = 70.0
DEFAULT_ELEVATION_M = 0
DEFAULT_AREA_ZOOM = 2


class AstronomyAPIError(Exception):
    """Raised when AstronomyAPI returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _auth_header(settings: Settings) -> str:
    token = base64.b64encode(
        f"{settings.astronomy_api_application_id}:{settings.astronomy_api_application_secret}".encode()
    ).decode()
    return f"Basic {token}"


def _normalize_time(time_value: str) -> str:
    if len(time_value) == 5:
        return f"{time_value}:00"
    return time_value


def _parse_time_parts(time_value: str) -> tuple[int, int, int]:
    parts = _normalize_time(time_value).split(":")
    return int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0


def _local_sidereal_time_hours(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    longitude_deg: float,
) -> float:
    """Compute local sidereal time in hours for zenith right ascension."""
    if month <= 2:
        year -= 1
        month += 12

    century = year // 100
    leap = 2 - century + century // 4
    julian_day = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + leap - 1524.5
    julian_day += (hour + minute / 60 + second / 3600) / 24

    julian_centuries = (julian_day - 2451545.0) / 36525.0
    gmst_deg = (
        280.46061837
        + 360.98564736629 * (julian_day - 2451545.0)
        + 0.000387933 * julian_centuries**2
        - julian_centuries**3 / 38710000.0
    )
    lst_deg = (gmst_deg + longitude_deg) % 360
    return lst_deg / 15.0


def _zenith_equatorial(latitude: float, longitude: float, date: str, time: str) -> tuple[float, float]:
    """Return equatorial coordinates (RA hours, Dec degrees) for the observer's zenith."""
    year, month, day = (int(part) for part in date.split("-"))
    hour, minute, second = _parse_time_parts(time)
    ra_hours = _local_sidereal_time_hours(year, month, day, hour, minute, second, longitude)
    return ra_hours, latitude


def _equatorial_from_positions(positions_data: dict, latitude: float) -> tuple[float, float, str]:
    """
    Pick equatorial center from body positions near zenith, or fall back to true zenith.

    Returns (right_ascension_hours, declination_degrees, source_label).
    """
    rows = positions_data.get("data", {}).get("table", {}).get("rows", [])
    best_altitude = -999.0
    best_ra_hours = 0.0
    best_dec_deg = latitude
    best_name = ""

    for row in rows:
        body_id = row.get("entry", {}).get("id", "")
        cells = row.get("cells", [])
        if not cells:
            continue

        cell = cells[0]
        altitude = float(cell["position"]["horizontal"]["altitude"]["degrees"])
        if body_id == "sun" and altitude < 0:
            continue

        if altitude > best_altitude:
            equatorial = cell["position"]["equatorial"]
            best_altitude = altitude
            best_ra_hours = float(equatorial["rightAscension"]["hours"])
            best_dec_deg = float(equatorial["declination"]["degrees"])
            best_name = row.get("entry", {}).get("name", body_id)

    if best_altitude >= NEAR_ZENITH_ALTITUDE_DEG:
        return best_ra_hours, best_dec_deg, best_name

    return 0.0, latitude, "zenith"


async def _fetch_body_positions(
    client: httpx.AsyncClient,
    settings: Settings,
    request: StarChartRequest,
) -> dict:
    """Fetch celestial body positions for the observer's date and time."""
    params = {
        "latitude": str(request.latitude),
        "longitude": str(request.longitude),
        "elevation": str(DEFAULT_ELEVATION_M),
        "from_date": request.date,
        "to_date": request.date,
        "time": _normalize_time(request.time),
    }
    headers = {"Authorization": _auth_header(settings)}

    response = await client.get(POSITIONS_URL, params=params, headers=headers)
    if response.status_code >= 400:
        raise AstronomyAPIError(
            f"AstronomyAPI positions request failed: {response.text}",
            status_code=response.status_code,
        )

    return response.json()


def _observer_payload(request: StarChartRequest) -> dict:
    return {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "date": request.date,
        "time": _normalize_time(request.time),
    }


async def _build_area_view(
    client: httpx.AsyncClient,
    settings: Settings,
    request: StarChartRequest,
) -> dict:
    """Build an area view centered on the sky near zenith using body positions."""
    positions_data = await _fetch_body_positions(client, settings, request)
    ra_hours, dec_deg, source = _equatorial_from_positions(positions_data, request.latitude)

    if source == "zenith":
        ra_hours, dec_deg = _zenith_equatorial(
            request.latitude,
            request.longitude,
            request.date,
            request.time,
        )

    return {
        "type": "area",
        "parameters": {
            "position": {
                "equatorial": {
                    "rightAscension": ra_hours,
                    "declination": dec_deg,
                }
            },
            "zoom": DEFAULT_AREA_ZOOM,
        },
    }


def _build_constellation_view(request: StarChartRequest) -> dict:
    if not request.constellation:
        raise AstronomyAPIError("Constellation ID is required for constellation view.")

    return {
        "type": "constellation",
        "parameters": {"constellation": request.constellation.lower()},
    }


async def generate_star_chart(settings: Settings, request: StarChartRequest) -> tuple[str, str]:
    """Generate a star chart and return the image URL and view type."""
    headers = {
        "Authorization": _auth_header(settings),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        if request.view_type == "constellation":
            view = _build_constellation_view(request)
            view_type_label = "constellation"
        else:
            view = await _build_area_view(client, settings, request)
            view_type_label = "area"

        payload = {
            "style": "default",
            "observer": _observer_payload(request),
            "view": view,
        }

        response = await client.post(STAR_CHART_URL, json=payload, headers=headers)

    if response.status_code == 401:
        raise AstronomyAPIError("Invalid AstronomyAPI credentials.", status_code=401)
    if response.status_code >= 400:
        raise AstronomyAPIError(
            f"AstronomyAPI request failed: {response.text}",
            status_code=response.status_code,
        )

    data = response.json()
    image_url = data.get("data", {}).get("imageUrl") or data.get("imageUrl")
    if not image_url:
        raise AstronomyAPIError("AstronomyAPI did not return an image URL.")

    return image_url, view_type_label

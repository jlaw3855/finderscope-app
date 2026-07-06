"""DSO visibility route tests."""

from unittest.mock import AsyncMock, patch

from app.config import Settings
from app.main import app
from app.models.dso_visibility import DsoDayVisibility, SiteSkyConditions
from app.routers import dso_visibility
from fastapi.testclient import TestClient


def test_dso_visibility_enabled_setting_default() -> None:
    settings = Settings(ipgeolocation_api_key="test-key")
    assert settings.dso_visibility_enabled is False


def _ensure_dso_router_registered() -> None:
    """Register DSO routes when the app started with dso_visibility_enabled=False."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/dso-visibility":
            return
    app.include_router(dso_visibility.router)


def test_dso_visibility_route_returns_payload(client: TestClient) -> None:
    _ensure_dso_router_registered()
    site = SiteSkyConditions(
        bortle=5,
        sqm=20.5,
        limiting_magnitude=5.6,
        source="lightpollutionmap",
    )

    with (
        patch(
            "app.routers.dso_visibility.lookup_site_darkness",
            AsyncMock(return_value=site),
        ),
        patch(
            "app.routers.dso_visibility.compute_dso_visibility",
            return_value=[DsoDayVisibility(date="2026-08-09", objects=[])],
        ),
    ):
        response = client.post(
            "/api/dso-visibility",
            json={
                "latitude": 39.7392,
                "longitude": -104.9903,
                "timezone": "America/Denver",
                "dates": ["2026-08-09"],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["site_sky"]["bortle"] == 5
    assert data["dso_visibility"][0]["date"] == "2026-08-09"

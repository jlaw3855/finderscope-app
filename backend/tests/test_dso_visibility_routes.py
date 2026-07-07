"""DSO visibility route tests."""

from unittest.mock import AsyncMock, patch

from app.models.dso_visibility import DsoDayVisibility, SiteSkyConditions
from fastapi.testclient import TestClient


def test_dso_visibility_route_returns_payload(client: TestClient) -> None:
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

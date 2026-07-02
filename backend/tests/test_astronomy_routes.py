"""Route tests for the astronomy summary API."""

from unittest.mock import patch

from app.models.astronomy import (
    AstronomyEvent,
    PlanetDayVisibility,
    PlanetVisibilityRow,
)
from fastapi.testclient import TestClient


class TestAstronomyRoute:
    @patch("app.routers.astronomy.search_astronomy_events")
    @patch("app.routers.astronomy.compute_planet_visibility")
    def test_astronomy_success(
        self,
        mock_visibility,
        mock_events,
        client: TestClient,
    ) -> None:
        mock_events.return_value = [
            AstronomyEvent(
                id="evt-1",
                category="opposition",
                title="Mars at opposition",
                start_at="2026-07-01T12:00:00Z",
                peak_at="2026-07-01T12:00:00Z",
                description="Mars is opposite the Sun.",
                visible_locally=True,
            )
        ]
        mock_visibility.return_value = [
            PlanetDayVisibility(
                date="2026-06-27",
                planets=[
                    PlanetVisibilityRow(
                        body="Jupiter",
                        visible=True,
                        windows_civil=[{"start": "20:00", "end": "04:00"}],
                        windows_astronomical=[{"start": "21:30", "end": "04:00"}],
                        peak_altitude_deg=45.0,
                        peak_at="23:00",
                        magnitude=-2.1,
                    )
                ],
            )
        ]

        response = client.post(
            "/api/astronomy",
            json={
                "latitude": 39.7392,
                "longitude": -104.9903,
                "timezone": "America/Denver",
                "dates": ["2026-06-27"],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["events"][0]["title"] == "Mars at opposition"
        assert payload["planet_visibility"][0]["planets"][0]["body"] == "Jupiter"

    def test_astronomy_rejects_invalid_latitude(self, client: TestClient) -> None:
        response = client.post(
            "/api/astronomy",
            json={
                "latitude": 95,
                "longitude": -104.9903,
                "timezone": "America/Denver",
                "dates": ["2026-06-27"],
            },
        )
        assert response.status_code == 422

    def test_astronomy_rejects_empty_dates(self, client: TestClient) -> None:
        response = client.post(
            "/api/astronomy",
            json={
                "latitude": 39.7392,
                "longitude": -104.9903,
                "timezone": "America/Denver",
                "dates": [],
            },
        )
        assert response.status_code == 422

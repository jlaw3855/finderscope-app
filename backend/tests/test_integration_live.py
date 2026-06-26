"""Opt-in integration tests against real external APIs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

VALID_RATINGS = {"Excellent", "Good", "Fair", "Poor"}


@pytest.fixture
def live_client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.live
def test_live_forecast_denver(live_client: TestClient) -> None:
    response = live_client.post("/api/forecast", json={"address": "Denver, CO"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["location"]["latitude"] is not None
    assert payload["location"]["longitude"] is not None
    assert len(payload["nights"]) == 7
    assert payload["nights"][0]["rating"] in VALID_RATINGS


@pytest.mark.live
def test_live_star_chart_constellation(live_client: TestClient) -> None:
    response = live_client.post(
        "/api/star-chart",
        json={
            "latitude": 39.7392,
            "longitude": -104.9903,
            "date": "2025-06-20",
            "time": "22:00",
            "view_type": "constellation",
            "constellation": "ori",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_url"].startswith("http")
    assert payload["view_type"] == "constellation"

"""Route tests with mocked external services."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestHealthRoute:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestForecastRoute:
    @patch("app.routers.forecast.openmeteo.fetch_forecast", new_callable=AsyncMock)
    @patch("app.routers.forecast.ipgeolocation.fetch_time_series", new_callable=AsyncMock)
    @patch("app.routers.forecast.ipgeolocation.resolve_location", new_callable=AsyncMock)
    def test_forecast_success(
        self,
        mock_resolve: AsyncMock,
        mock_time_series: AsyncMock,
        mock_weather: AsyncMock,
        client: TestClient,
        load_fixture,
    ) -> None:
        mock_resolve.return_value = load_fixture("location.json")
        mock_time_series.return_value = load_fixture("time_series.json")
        mock_weather.return_value = load_fixture("weather.json")

        response = client.post("/api/forecast", json={"address": "Denver, CO"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["location"]["label"] == "Denver, Colorado, United States"
        assert len(payload["nights"]) == 2
        assert payload["nights"][0]["rating"] in {"Excellent", "Good", "Fair", "Poor"}

    def test_forecast_rejects_empty_address(self, client: TestClient) -> None:
        response = client.post("/api/forecast", json={"address": ""})
        assert response.status_code == 422


class TestStarChartRoute:
    @patch(
        "app.routers.star_chart.astronomyapi.generate_star_chart",
        new_callable=AsyncMock,
    )
    def test_star_chart_success(self, mock_generate: AsyncMock, client: TestClient) -> None:
        mock_generate.return_value = ("https://example.com/chart.png", "all-sky")

        response = client.post(
            "/api/star-chart",
            json={
                "latitude": 39.7392,
                "longitude": -104.9903,
                "date": "2025-06-20",
                "time": "22:00",
                "view_type": "all-sky",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["image_url"] == "https://example.com/chart.png"
        assert payload["view_type"] == "all-sky"

    def test_star_chart_rejects_invalid_latitude(self, client: TestClient) -> None:
        response = client.post(
            "/api/star-chart",
            json={
                "latitude": 95,
                "longitude": -104.9903,
                "date": "2025-06-20",
                "time": "22:00",
                "view_type": "all-sky",
            },
        )
        assert response.status_code == 422

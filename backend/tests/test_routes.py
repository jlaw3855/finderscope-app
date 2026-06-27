"""Route tests with mocked external services."""

from datetime import date
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.services import ipgeolocation


class TestHealthRoute:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestForecastRoute:
    @patch("app.routers.forecast.ipgeolocation.time_series_date_range")
    @patch("app.routers.forecast.ipgeolocation.default_date_range")
    @patch("app.routers.forecast.openmeteo.fetch_forecast", new_callable=AsyncMock)
    @patch("app.routers.forecast.ipgeolocation.fetch_time_series", new_callable=AsyncMock)
    @patch("app.routers.forecast.ipgeolocation.resolve_location", new_callable=AsyncMock)
    def test_forecast_success(
        self,
        mock_resolve: AsyncMock,
        mock_time_series: AsyncMock,
        mock_weather: AsyncMock,
        mock_default_range,
        mock_time_series_range,
        client: TestClient,
        load_fixture,
    ) -> None:
        mock_resolve.return_value = load_fixture("location.json")
        mock_time_series.return_value = load_fixture("time_series.json")
        mock_weather.return_value = load_fixture("weather.json")
        forecast_start = date(2025, 6, 20)
        forecast_end = date(2025, 6, 21)
        mock_default_range.return_value = (forecast_start, forecast_end)
        mock_time_series_range.return_value = (date(2025, 6, 19), forecast_end)

        response = client.post("/api/forecast", json={"address": "Denver, CO"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["location"]["label"] == "Denver, Colorado, United States"
        assert len(payload["nights"]) == 2
        assert payload["nights"][0]["rating"] in {"Excellent", "Good", "Fair", "Poor"}

        mock_time_series.assert_awaited_once_with(
            mock_time_series.call_args[0][0],
            payload["location"]["latitude"],
            payload["location"]["longitude"],
            date(2025, 6, 19),
            forecast_end,
        )
        mock_weather.assert_awaited_once_with(
            payload["location"]["latitude"],
            payload["location"]["longitude"],
            forecast_days=ipgeolocation.weather_forecast_days(forecast_start, forecast_end),
        )

    def test_forecast_rejects_empty_address(self, client: TestClient) -> None:
        response = client.post("/api/forecast", json={"address": ""})
        assert response.status_code == 422


"""Route tests with mocked external services."""

from datetime import date
from unittest.mock import AsyncMock, patch

from app.services import ipgeolocation
from app.version import read_version
from fastapi.testclient import TestClient


class TestHealthRoute:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": read_version()}


class TestForecastRoute:
    @patch("app.routers.forecast.seventimer.fetch_astro_forecast", new_callable=AsyncMock)
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
        mock_astro: AsyncMock,
        client: TestClient,
        load_fixture,
    ) -> None:
        mock_resolve.return_value = load_fixture("location.json")
        mock_time_series.return_value = load_fixture("time_series.json")
        mock_weather.return_value = load_fixture("weather.json")
        mock_astro.return_value = None
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

    @patch("app.routers.forecast.seventimer.fetch_astro_forecast", new_callable=AsyncMock)
    def test_forecast_fail_open_when_7timer_fails(
        self,
        mock_astro: AsyncMock,
        client: TestClient,
        load_fixture,
    ) -> None:
        from app.services.seventimer import SevenTimerError

        with (
            patch(
                "app.routers.forecast.ipgeolocation.resolve_location",
                new_callable=AsyncMock,
                return_value=load_fixture("location.json"),
            ),
            patch(
                "app.routers.forecast.ipgeolocation.fetch_time_series",
                new_callable=AsyncMock,
                return_value=load_fixture("time_series.json"),
            ),
            patch(
                "app.routers.forecast.openmeteo.fetch_forecast",
                new_callable=AsyncMock,
                return_value=load_fixture("weather.json"),
            ),
            patch(
                "app.routers.forecast.ipgeolocation.default_date_range",
                return_value=(date(2025, 6, 20), date(2025, 6, 21)),
            ),
            patch(
                "app.routers.forecast.ipgeolocation.time_series_date_range",
                return_value=(date(2025, 6, 19), date(2025, 6, 21)),
            ),
        ):
            mock_astro.side_effect = SevenTimerError("upstream down")

            response = client.post("/api/forecast", json={"address": "Denver, CO"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["nights"][0]["astro_forecast_limited"] is True
        assert payload["astro_data_unavailable"] is True

    def test_forecast_rejects_empty_address(self, client: TestClient) -> None:
        response = client.post("/api/forecast", json={"address": ""})
        assert response.status_code == 422


class TestApodRoute:
    @patch("app.routers.apod.get_apod", new_callable=AsyncMock)
    def test_apod_success(self, mock_get_apod: AsyncMock, client: TestClient, load_fixture) -> None:
        from app.services.nasa_apod import _parse_apod_payload

        mock_get_apod.return_value = _parse_apod_payload(load_fixture("apod_response.json"))

        response = client.get("/api/apod")

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "Starlink over Orion"
        assert payload["media_type"] == "image"
        assert payload["image_url"] is not None
        assert payload["copyright"] == "Robert Gendler"

    def test_apod_rejects_invalid_date(self, client: TestClient) -> None:
        response = client.get("/api/apod", params={"date": "not-a-date"})
        assert response.status_code == 422


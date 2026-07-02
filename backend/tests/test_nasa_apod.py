"""Unit tests for NASA APOD client and caching."""

import json
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.nasa_apod import (
    NasaApodError,
    _current_apod_day,
    _parse_apod_payload,
    clear_apod_cache,
    fetch_apod,
    get_apod,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "apod_response.json"


@pytest.fixture
def apod_payload() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    clear_apod_cache()
    yield
    clear_apod_cache()


class TestCurrentApodDay:
    def test_before_reset_uses_previous_calendar_day(self) -> None:
        assert _current_apod_day(now=datetime(2025, 6, 21, 3, 59, tzinfo=UTC)) == date(2025, 6, 20)

    def test_at_reset_uses_current_calendar_day(self) -> None:
        assert _current_apod_day(now=datetime(2025, 6, 21, 4, 0, tzinfo=UTC)) == date(2025, 6, 21)

    def test_after_reset_uses_current_calendar_day(self) -> None:
        assert _current_apod_day(now=datetime(2025, 6, 21, 15, 30, tzinfo=UTC)) == date(2025, 6, 21)


class TestParseApodPayload:
    def test_parses_image_payload(self, apod_payload: dict) -> None:
        parsed = _parse_apod_payload(apod_payload)
        assert parsed.title == "Starlink over Orion"
        assert parsed.date == "2025-06-20"
        assert parsed.media_type == "image"
        assert parsed.image_url == apod_payload["hdurl"]
        assert parsed.video_url is None
        assert parsed.copyright == "Robert Gendler"

    def test_prefers_hdurl_for_images(self) -> None:
        parsed = _parse_apod_payload(
            {
                "title": "Sample",
                "date": "2025-01-01",
                "explanation": "Sample explanation.",
                "media_type": "image",
                "url": "https://example.com/low.jpg",
                "hdurl": "https://example.com/high.jpg",
            }
        )
        assert parsed.image_url == "https://example.com/high.jpg"

    def test_parses_video_payload(self) -> None:
        parsed = _parse_apod_payload(
            {
                "title": "Sample Video",
                "date": "2025-01-02",
                "explanation": "Video explanation.",
                "media_type": "video",
                "url": "https://www.youtube.com/watch?v=abc123",
            }
        )
        assert parsed.media_type == "video"
        assert parsed.video_url == "https://www.youtube.com/watch?v=abc123"
        assert parsed.image_url is None

    def test_strips_sky_surprise_footer(self) -> None:
        parsed = _parse_apod_payload(
            {
                "title": "Sample",
                "date": "2025-01-01",
                "explanation": (
                    "Main APOD caption about the image. "
                    "Sky Surprise: What picture did APOD feature on your birthday? (after 1995)"
                ),
                "media_type": "image",
                "url": "https://example.com/apod.jpg",
            }
        )
        assert parsed.explanation == "Main APOD caption about the image."
        assert "Sky Surprise" not in parsed.explanation

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(NasaApodError):
            _parse_apod_payload({"title": "Incomplete"})


class TestFetchApod:
    @pytest.mark.asyncio
    async def test_fetch_apod_success(self, apod_payload: dict) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = apod_payload

        with patch(
            "app.services.nasa_apod.get_http_client",
            return_value=MagicMock(get=AsyncMock(return_value=mock_response)),
        ):
            parsed = await fetch_apod("DEMO_KEY", day=date(2025, 6, 20))

        assert parsed.title == "Starlink over Orion"

    @pytest.mark.asyncio
    async def test_fetch_apod_http_error(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with patch(
            "app.services.nasa_apod.get_http_client",
            return_value=MagicMock(get=AsyncMock(return_value=mock_response)),
        ):
            with pytest.raises(NasaApodError):
                await fetch_apod("DEMO_KEY", day=date(2025, 6, 20))


class TestGetApodCache:
    @pytest.mark.asyncio
    async def test_get_apod_uses_cache(self, apod_payload: dict) -> None:
        with patch(
            "app.services.nasa_apod.fetch_apod",
            new_callable=AsyncMock,
            return_value=_parse_apod_payload(apod_payload),
        ) as mock_fetch:
            first = await get_apod("DEMO_KEY", day=date(2025, 6, 20))
            second = await get_apod("DEMO_KEY", day=date(2025, 6, 20))

        assert first.title == second.title
        mock_fetch.assert_awaited_once()

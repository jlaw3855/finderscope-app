"""Tests for light pollution conversion and lookup."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services import light_pollution
from app.services.light_pollution import (
    FALLBACK_SITE,
    artificial_brightness_to_sqm,
    lookup_site_darkness,
    parse_query_raster_response,
    sqm_to_bortle,
    sqm_to_nelm,
)


def test_sqm_to_bortle() -> None:
    assert sqm_to_bortle(21.9) == 1
    assert sqm_to_bortle(20.5) == 5
    assert sqm_to_bortle(18.0) == 9


def test_sqm_to_nelm_increases_with_darker_sky() -> None:
    dark = sqm_to_nelm(21.9)
    bright = sqm_to_nelm(19.0)
    assert dark > bright


def test_artificial_brightness_to_sqm() -> None:
    sqm = artificial_brightness_to_sqm(0.5)
    assert 19.0 < sqm < 21.0


def test_parse_query_raster_response() -> None:
    assert parse_query_raster_response("0.8;1.7;7.6;26.4,205") == pytest.approx(26.4)


@pytest.mark.asyncio
async def test_lookup_site_darkness_uses_cache() -> None:
    light_pollution._CACHE.clear()
    mock_fetch = AsyncMock(return_value=0.2)
    with patch(
        "app.services.light_pollution._fetch_artificial_brightness",
        mock_fetch,
    ):
        first = await lookup_site_darkness(39.7392, -104.9903)
        second = await lookup_site_darkness(39.7392, -104.9903)
    assert first.source == "lightpollutionmap"
    assert second == first
    mock_fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_site_darkness_fallback_on_error() -> None:
    light_pollution._CACHE.clear()
    with patch(
        "app.services.light_pollution._fetch_artificial_brightness",
        AsyncMock(side_effect=TimeoutError("timeout")),
    ):
        site = await lookup_site_darkness(51.0, 10.0)
    assert site.source == "fallback"
    assert site.bortle == FALLBACK_SITE.bortle

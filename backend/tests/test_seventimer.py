"""Unit tests for 7timer ASTRO client and indexing."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.seventimer import (
    SevenTimerError,
    build_astro_index,
    categorical_astro_score,
    fetch_astro_forecast,
    lookup_astro_at,
    parse_init_utc,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "seventimer_astro.json"


@pytest.fixture
def astro_payload() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def denver_index(astro_payload: dict):
    return build_astro_index(astro_payload, "America/Denver")


class TestParseInit:
    def test_parse_init_utc(self) -> None:
        init = parse_init_utc("2026062812")
        assert init.year == 2026
        assert init.month == 6
        assert init.day == 28
        assert init.hour == 12


class TestFetchAstroForecast:
    @pytest.mark.asyncio
    async def test_invalid_json_raises_seventimer_error(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("app.services.seventimer.get_http_client", return_value=mock_client):
            with pytest.raises(SevenTimerError, match="invalid or empty JSON"):
                await fetch_astro_forecast(36.601, -121.895)


class TestCategoricalAstroScore:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(1, 100.0), (8, 0.0), (4, pytest.approx(57.142857, rel=1e-4)), (None, None)],
    )
    def test_bins(self, value: int | None, expected) -> None:
        assert categorical_astro_score(value) == expected


class TestBuildAstroIndex:
    def test_builds_buckets(self, denver_index) -> None:
        assert len(denver_index.buckets) == 24
        assert denver_index.buckets[0].seeing is not None
        assert denver_index.buckets[0].transparency is not None


class TestLookupAstroAt:
    def test_nearest_bucket_within_window(self, denver_index) -> None:
        slot = denver_index.buckets[0].at_local
        seeing, transparency = lookup_astro_at(slot, denver_index)
        assert seeing == denver_index.buckets[0].seeing
        assert transparency == denver_index.buckets[0].transparency

    def test_outside_valid_window_returns_none(self, denver_index) -> None:
        slot = denver_index.valid_until_local + timedelta(hours=1)
        seeing, transparency = lookup_astro_at(slot, denver_index)
        assert seeing is None
        assert transparency is None

    def test_none_index_returns_none(self) -> None:
        assert lookup_astro_at(datetime(2026, 6, 28, 22, 0), None) == (None, None)

"""Tests for Noctua-backed astronomy event enrichment."""

from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.models.astronomy import AstronomyEvent
from app.services import astronomy_enrichment


def _event(**kwargs) -> AstronomyEvent:
    defaults = {
        "id": "evt-1",
        "category": "opposition",
        "title": "Mars at opposition",
        "start_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "peak_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "end_at": None,
        "description": "Mars is opposite the Sun.",
        "visible_locally": True,
    }
    defaults.update(kwargs)
    return AstronomyEvent(**defaults)


class TestSkysourceKeysForEvent:
    def test_lunar_eclipse_uses_moon(self) -> None:
        event = _event(category="lunar_eclipse", title="Total Lunar Eclipse")
        assert astronomy_enrichment.skysource_keys_for_event(event) == ["Moon"]

    def test_planet_conjunction_uses_both_bodies(self) -> None:
        event = _event(
            category="conjunction",
            title="Venus and Jupiter conjunction",
        )
        assert astronomy_enrichment.skysource_keys_for_event(event) == ["Venus", "Jupiter"]

    def test_meteor_shower_uses_constellation_from_title(self) -> None:
        event = _event(
            category="meteor_shower",
            title="Perseids (Perseus)",
        )
        assert astronomy_enrichment.skysource_keys_for_event(event) == ["Perseus"]


@pytest.mark.asyncio
class TestEnrichAstronomyEvents:
    async def test_disabled_returns_events_unchanged(self) -> None:
        events = [_event()]
        settings = Settings(
            ipgeolocation_api_key="test",
            noctua_enrichment_enabled=False,
        )
        result = await astronomy_enrichment.enrich_astronomy_events(events, settings)
        assert result[0].subjects == []

    async def test_attaches_subjects_from_noctua(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_fetch(_settings, name: str):
            if name == "Mars":
                return {
                    "short_name": "Mars",
                    "types": ["Pla", "SSO"],
                    "interest": 4.5,
                    "names": ["NAME Mars"],
                    "model": "jpl_sso",
                }
            return None

        monkeypatch.setattr(astronomy_enrichment.noctua, "fetch_skysource_by_name", fake_fetch)
        monkeypatch.setattr(astronomy_enrichment.noctua, "search_skysources", lambda *args, **kwargs: [])

        settings = Settings(
            ipgeolocation_api_key="test",
            noctua_enrichment_enabled=True,
        )
        result = await astronomy_enrichment.enrich_astronomy_events([_event()], settings)
        assert len(result[0].subjects) == 1
        assert result[0].subjects[0].short_name == "Mars"
        assert result[0].subjects[0].types == ["Pla", "SSO"]

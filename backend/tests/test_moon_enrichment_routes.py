"""Route tests for moon enrichment endpoints."""

from pathlib import Path

import pytest

from app.services import freeastroapi, moon_cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(moon_cache, "_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(moon_cache, "_db_path", lambda: tmp_path / "moon.db")
    monkeypatch.setattr(moon_cache, "_quota_path", lambda: tmp_path / "quota.json")
    monkeypatch.setattr(moon_cache, "_svg_dir", lambda: tmp_path / "svg")


class TestMoonEnrichmentRoutes:
    def test_unavailable_without_api_key(self, client, fake_settings, monkeypatch) -> None:
        monkeypatch.setattr(fake_settings, "freeastro_api_key", None)
        monkeypatch.setattr(fake_settings, "moon_enrichment_enabled", False)
        response = client.get(
            "/api/moon/enrichment",
            params={"dates": "2025-06-20,2025-06-21", "timezone": "America/Denver"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "unavailable"
        assert payload["cached_count"] == 0

    def test_complete_when_cache_warm(self, client, fake_settings, monkeypatch) -> None:
        monkeypatch.setattr(fake_settings, "freeastro_api_key", "test-freeastro-key")
        theme_key = freeastroapi.theme_hash(
            fake_settings.moon_visual_moon_color,
            fake_settings.moon_visual_shadow_color,
        )
        moon_cache.store_cached(
            date="2025-06-20",
            theme_key=theme_key,
            phase_name="Waxing Gibbous",
            illumination_pct=94.0,
            age_days=12.4,
            is_waxing=True,
            special_labels=["Blue Moon"],
            svg="<svg viewBox='0 0 100 100'></svg>",
        )

        response = client.get(
            "/api/moon/enrichment",
            params={"dates": "2025-06-20", "timezone": "America/Denver"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "complete"
        assert payload["cached_count"] == 1
        assert payload["entries"][0]["phase_name"] == "Waxing Gibbous"
        assert payload["entries"][0]["visual_url"] == "/api/moon/visual/2025-06-20.svg?profile=noon"

        svg_response = client.get("/api/moon/visual/2025-06-20.svg", params={"profile": "noon"})
        assert svg_response.status_code == 200
        assert svg_response.headers["content-type"].startswith("image/svg+xml")

    def test_pending_when_cache_cold(self, client, fake_settings, monkeypatch) -> None:
        monkeypatch.setattr(fake_settings, "freeastro_api_key", "test-freeastro-key")

        async def _noop_fetch(*_args, **_kwargs):
            return None

        monkeypatch.setattr(
            "app.services.moon_enrichment_queue.fetch_and_cache_date",
            _noop_fetch,
        )

        response = client.get(
            "/api/moon/enrichment",
            params={"dates": "2025-06-21", "timezone": "America/Denver"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "pending"
        assert payload["pending_dates"] == ["2025-06-21"]

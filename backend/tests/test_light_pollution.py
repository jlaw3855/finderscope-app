"""Tests for light pollution conversion and grid lookup."""

from pathlib import Path

import pytest
from app.services import light_pollution
from app.services.light_pollution import (
    FALLBACK_SITE,
    GRID_SOURCE,
    LightPollutionGrid,
    artificial_brightness_to_sqm,
    clear_light_pollution_caches,
    load_light_pollution_grid,
    lookup_site_darkness,
    sample_artificial_brightness,
    sqm_to_bortle,
    sqm_to_nelm,
)

FIXTURE_GRID = Path(__file__).resolve().parent / "fixtures" / "light_pollution_grid_sample.json"


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


def test_load_light_pollution_grid_validates_fixture() -> None:
    clear_light_pollution_caches()
    grid = load_light_pollution_grid(str(FIXTURE_GRID))
    assert grid.rows == 18
    assert grid.cols == 36
    assert grid.resolution_deg == 10.0


def test_sample_artificial_brightness_bilinear() -> None:
    grid = LightPollutionGrid(
        source="test",
        resolution_deg=1.0,
        west=0.0,
        south=0.0,
        rows=2,
        cols=2,
        nodata=-1.0,
        values=(0.0, 10.0, 10.0, 20.0),
    )
    assert sample_artificial_brightness(0.5, 0.5, grid) == pytest.approx(10.0)
    assert sample_artificial_brightness(0.0, 0.0, grid) == pytest.approx(0.0)


def test_sample_artificial_brightness_returns_none_for_nodata() -> None:
    grid = LightPollutionGrid(
        source="test",
        resolution_deg=1.0,
        west=0.0,
        south=0.0,
        rows=2,
        cols=2,
        nodata=-1.0,
        values=(-1.0, 10.0, 10.0, 20.0),
    )
    assert sample_artificial_brightness(0.5, 0.5, grid) is None


def test_lookup_site_darkness_uses_cache() -> None:
    clear_light_pollution_caches()
    first = lookup_site_darkness(39.7392, -104.9903, grid_path=str(FIXTURE_GRID))
    second = lookup_site_darkness(39.7392, -104.9903, grid_path=str(FIXTURE_GRID))
    assert first.source == GRID_SOURCE
    assert second == first


def test_lookup_site_darkness_fallback_on_missing_file() -> None:
    clear_light_pollution_caches()
    site = lookup_site_darkness(51.0, 10.0, grid_path="data/light_pollution/does_not_exist.json")
    assert site.source == "fallback"
    assert site.bortle == FALLBACK_SITE.bortle


def test_lookup_site_darkness_differentiates_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_light_pollution_caches()
    dark = lookup_site_darkness(0.0, 0.0, grid_path=str(FIXTURE_GRID))
    bright = lookup_site_darkness(39.7392, -104.9903, grid_path=str(FIXTURE_GRID))
    assert dark.sqm == bright.sqm
    assert dark.bortle == bright.bortle

    gradient = LightPollutionGrid(
        source="test",
        resolution_deg=1.0,
        west=-180.0,
        south=-90.0,
        rows=180,
        cols=360,
        nodata=-1.0,
        values=tuple(
            0.05 if col < 180 else 50.0
            for row in range(180)
            for col in range(360)
        ),
    )
    light_pollution.load_light_pollution_grid.cache_clear()
    monkeypatch.setattr(
        light_pollution,
        "load_light_pollution_grid",
        lambda _path: gradient,
    )
    rural = lookup_site_darkness(45.0, -120.0, grid_path="ignored")
    urban = lookup_site_darkness(45.0, 10.0, grid_path="ignored")
    assert rural.sqm > urban.sqm
    assert rural.bortle < urban.bortle

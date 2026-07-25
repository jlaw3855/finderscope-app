"""Tests for DSO visibility computation."""

from pathlib import Path

from app.models.dso_visibility import SiteSkyConditions
from app.services.dso_visibility import compute_dso_visibility
from app.services.openngc_catalog import load_openngc_catalog_from_path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES_DIR / "openngc_sample.csv"

DENVER_LAT = 39.7392
DENVER_LON = -104.9903
DENVER_TZ = "America/Denver"

SUBURBAN_SITE = SiteSkyConditions(
    bortle=5,
    sqm=20.5,
    limiting_magnitude=5.6,
    source="fallback",
)


def test_compute_dso_visibility_returns_top_objects_for_sample_catalog() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        SUBURBAN_SITE,
        catalog=catalog,
    )
    assert len(results) == 1
    day = results[0]
    assert day.date == "2026-08-09"
    assert 0 < len(day.objects) <= 10
    names = {row.name for row in day.objects}
    assert "NGC0224" in names


def test_compute_dso_visibility_row_has_timeline_fields() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        SUBURBAN_SITE,
        catalog=catalog,
    )
    row = results[0].objects[0]
    assert row.visible is True
    assert len(row.windows_astronomical) >= 1
    assert row.peak_altitude_deg is not None
    assert row.peak_at is not None
    assert row.contrast > 0
    assert row.visibility_score > 0


def test_compute_dso_visibility_peak_falls_in_astronomical_window() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        SUBURBAN_SITE,
        catalog=catalog,
    )
    for row in results[0].objects:
        if not row.visible or row.peak_at is None:
            continue
        peak_minutes = _hm_to_minutes(row.peak_at)
        assert any(
            _hm_to_minutes(window.start) <= peak_minutes <= _hm_to_minutes(window.end)
            for window in row.windows_astronomical
        )


def _hm_to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def test_compute_dso_visibility_empty_when_nothing_detectable() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    bright_site = SiteSkyConditions(
        bortle=9,
        sqm=17.5,
        limiting_magnitude=0.5,
        source="fallback",
    )
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        bright_site,
        catalog=catalog,
    )
    assert results[0].objects == []


def test_compute_dso_visibility_populates_messier_field() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        SUBURBAN_SITE,
        catalog=catalog,
    )
    andromeda = next(row for row in results[0].objects if row.name == "NGC0224")
    assert andromeda.messier == 1


def test_compute_dso_visibility_messier_objects_can_rank_in_top_ten() -> None:
    catalog = load_openngc_catalog_from_path(SAMPLE_CSV)
    results = compute_dso_visibility(
        DENVER_LAT,
        DENVER_LON,
        DENVER_TZ,
        ["2026-08-09"],
        SUBURBAN_SITE,
        catalog=catalog,
    )
    messier_rows = [row for row in results[0].objects if row.messier is not None]
    assert len(messier_rows) > 0

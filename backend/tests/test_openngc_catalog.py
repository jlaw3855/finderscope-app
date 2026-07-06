"""Tests for OpenNGC catalog parsing."""

from pathlib import Path

import pytest
from app.services.openngc_catalog import (
    load_openngc_catalog_from_path,
    max_altitude_at_latitude,
    parse_dec_deg,
    parse_openngc_row,
    parse_ra_hours,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES_DIR / "openngc_sample.csv"


def test_parse_ra_hours() -> None:
    assert parse_ra_hours("00:42:44.31") == pytest.approx(0.712308611, rel=1e-6)
    assert parse_ra_hours("13:29:52.7") == pytest.approx(13.497972222, rel=1e-6)


def test_parse_dec_deg() -> None:
    assert parse_dec_deg("+41:16:09.4") == pytest.approx(41.269277, rel=1e-6)
    assert parse_dec_deg("-27:42:30") == pytest.approx(-27.708333, rel=1e-6)


def test_parse_openngc_row_filters_stars_and_nonexistent() -> None:
    star_row = {"Name": "IC0001", "Type": "**", "RA": "00:08:27.05", "Dec": "+27:43:03.6"}
    assert parse_openngc_row(star_row) is None

    nonex_row = {
        "Name": "NGC0001",
        "Type": "NonEx",
        "RA": "00:07:15.9",
        "Dec": "+27:42:30",
    }
    assert parse_openngc_row(nonex_row) is None


def test_parse_openngc_row_galaxy() -> None:
    row = {
        "Name": "NGC0224",
        "Type": "G",
        "RA": "00:42:44.31",
        "Dec": "+41:16:09.4",
        "V-Mag": "3.44",
        "B-Mag": "5.36",
        "SurfBr": "13.5",
        "Common names": "Andromeda Galaxy",
        "M": "1",
    }
    entry = parse_openngc_row(row)
    assert entry is not None
    assert entry.name == "NGC0224"
    assert entry.v_mag == pytest.approx(3.44)
    assert entry.surf_br == pytest.approx(13.5)
    assert entry.common_name == "Andromeda Galaxy"
    assert entry.messier == 1


def test_load_sample_catalog() -> None:
    entries = load_openngc_catalog_from_path(SAMPLE_CSV)
    names = {entry.name for entry in entries}
    assert "NGC0224" in names
    assert "NGC5194" in names
    assert "M0045" in names
    assert "IC0001" not in names
    assert "NGC0001" not in names
    assert len(entries) == 4


def test_max_altitude_at_latitude() -> None:
    assert max_altitude_at_latitude(41.0, 39.7) == pytest.approx(88.7, rel=1e-3)
    assert max_altitude_at_latitude(-30.0, 45.0) == pytest.approx(15.0, rel=1e-3)

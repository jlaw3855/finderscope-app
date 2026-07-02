"""Tests for FreeAstro moon phase client."""

from datetime import date

import pytest
from app.services.freeastroapi import (
    local_noon_date_param,
    moon_sample_date_param,
    normalize_phase_display_name,
    parse_moon_phase_response,
    theme_hash,
)


class TestThemeHash:
    def test_stable_hash(self) -> None:
        assert theme_hash("#E0E0E0", "#1a2030") == theme_hash("#E0E0E0", "#1a2030")
        assert theme_hash("#E0E0E0", "#1a2030") != theme_hash("#FFFFFF", "#1a2030")


class TestLocalNoonDateParam:
    def test_iso_local_noon(self) -> None:
        assert local_noon_date_param(date(2025, 6, 20)) == "2025-06-20T12:00:00"


class TestMoonSampleDateParam:
    def test_uses_custom_sample_datetime(self) -> None:
        assert (
            moon_sample_date_param(date(2025, 6, 20), "2025-06-21T01:07:00")
            == "2025-06-21T01:07:00"
        )

    def test_falls_back_to_noon(self) -> None:
        assert moon_sample_date_param(date(2025, 6, 20), None) == "2025-06-20T12:00:00"


class TestNormalizePhaseDisplayName:
    def test_near_full_waxing_gibbous(self) -> None:
        assert (
            normalize_phase_display_name("Waxing Gibbous", 99.8, 14.6) == "Full Moon"
        )

    def test_near_full_waning_gibbous(self) -> None:
        assert (
            normalize_phase_display_name("Waning Gibbous", 99.3, 15.5) == "Full Moon"
        )

    def test_early_waxing_gibbous_stays_gibbous(self) -> None:
        assert (
            normalize_phase_display_name("Waxing Gibbous", 98.5, 13.7) == "Waxing Gibbous"
        )

    def test_last_quarter_unchanged(self) -> None:
        assert normalize_phase_display_name("Last Quarter", 50.0, 22.1) == "Last Quarter"


class TestParseMoonPhaseResponse:
    def test_parses_phase_and_visual(self) -> None:
        payload = {
            "phase": {
                "name": "Waxing Gibbous",
                "illumination": 0.94,
                "age_days": 12.4,
                "is_waxing": True,
            },
            "special_moon": {"labels": ["Blue Moon"]},
            "moon_visual": {"type": "svg", "svg": "<svg></svg>"},
        }
        result = parse_moon_phase_response(payload, "2025-06-20")
        assert result.phase_name == "Waxing Gibbous"
        assert result.illumination_pct == pytest.approx(94.0)
        assert result.age_days == pytest.approx(12.4)
        assert result.is_waxing is True
        assert result.special_labels == ["Blue Moon"]
        assert result.svg == "<svg></svg>"

    def test_normalizes_near_full_gibbous(self) -> None:
        payload = {
            "phase": {
                "name": "Waxing Gibbous",
                "illumination": 0.998,
                "age_days": 14.6,
                "is_waxing": True,
            },
            "special_moon": {"labels": []},
            "moon_visual": {"type": "svg", "svg": "<svg></svg>"},
        }
        result = parse_moon_phase_response(payload, "2025-06-29")
        assert result.phase_name == "Full Moon"

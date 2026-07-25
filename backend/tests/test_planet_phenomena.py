"""Tests for Jupiter moons and Saturn ring tilt enrichment."""

from app.services.planet_phenomena import (
    compute_jupiter_moons,
    compute_saturn_ring_tilt,
)
from astronomy import Observer


class TestPlanetPhenomena:
    def test_saturn_ring_tilt_within_expected_range(self) -> None:
        observer = Observer(39.7392, -104.9903, 0.0)
        tilt, note = compute_saturn_ring_tilt(
            observer,
            "2026-06-27",
            "23:00",
            "America/Denver",
        )
        assert tilt is not None
        assert 0.0 <= tilt <= 27.0
        assert note in {"Edge-on", "Moderately open", "Wide open"}

    def test_jupiter_moons_returns_four_offsets_when_visible(self) -> None:
        observer = Observer(39.7392, -104.9903, 0.0)
        detail = compute_jupiter_moons(
            observer,
            "2026-06-27",
            "23:00",
            "America/Denver",
        )
        assert detail is not None
        assert detail.sampled_at == "23:00"
        assert len(detail.moons) == 4
        names = {moon.name for moon in detail.moons}
        assert names == {"Io", "Europa", "Ganymede", "Callisto"}
        for moon in detail.moons:
            assert abs(moon.east_arcmin) < 30
            assert abs(moon.north_arcmin) < 30

    def test_jupiter_moons_none_when_peak_missing(self) -> None:
        observer = Observer(39.7392, -104.9903, 0.0)
        assert (
            compute_jupiter_moons(observer, "2026-06-27", "invalid", "America/Denver")
            is None
        )

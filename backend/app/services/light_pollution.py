"""Site sky darkness lookup via prebuilt World Atlas 2015 light pollution grid."""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.models.dso_visibility import SiteSkyConditions

logger = logging.getLogger(__name__)

NATURAL_BACKGROUND_MCD_M2 = 0.171168465
MCD_M2_TO_TOTAL_DIVISOR = 108_000_000.0
GRID_SOURCE = "world_atlas_2015"

# * Standard SQM (mag/arcsec²) to Bortle class thresholds.
SQM_BORTLE_THRESHOLDS: tuple[tuple[float, int], ...] = (
    (21.75, 1),
    (21.50, 2),
    (21.25, 3),
    (21.00, 4),
    (20.50, 5),
    (20.00, 6),
    (19.50, 7),
    (18.50, 8),
)

FALLBACK_SITE = SiteSkyConditions(
    bortle=5,
    sqm=20.5,
    limiting_magnitude=5.6,
    source="fallback",
)

_CACHE: dict[str, tuple[float, SiteSkyConditions]] = {}
_CACHE_TTL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class LightPollutionGrid:
    """Row-major World Atlas artificial radiance grid (mcd/m²)."""

    source: str
    resolution_deg: float
    west: float
    south: float
    rows: int
    cols: int
    nodata: float
    values: tuple[float, ...]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_grid_path(grid_path: str | Path) -> Path:
    """Resolve a grid path relative to the backend root when not absolute."""
    configured = Path(grid_path)
    if configured.is_absolute():
        return configured
    return _backend_root() / configured


def sqm_to_bortle(sqm: float) -> int:
    """Map zenith SQM to Bortle scale (1 = darkest, 9 = brightest)."""
    for threshold, bortle in SQM_BORTLE_THRESHOLDS:
        if sqm >= threshold:
            return bortle
    return 9


def sqm_to_nelm(sqm: float) -> float:
    """Estimate naked-eye limiting magnitude from SQM using Unihedron formula."""
    return round(7.93 - 5.0 * math.log10(math.pow(10, 4.316 - sqm / 5.0) + 1.0), 2)


def artificial_brightness_to_sqm(artificial_brightness_mcd_m2: float) -> float:
    """Convert World Atlas artificial brightness to zenith SQM."""
    total = artificial_brightness_mcd_m2 + NATURAL_BACKGROUND_MCD_M2
    return round(math.log10(total / MCD_M2_TO_TOTAL_DIVISOR) / -0.4, 2)


def _cache_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.3f},{longitude:.3f}"


def _validate_grid_metadata(grid: LightPollutionGrid) -> None:
    expected_rows = round(180.0 / grid.resolution_deg)
    expected_cols = round(360.0 / grid.resolution_deg)
    if grid.rows != expected_rows or grid.cols != expected_cols:
        raise ValueError(
            "Grid rows/cols do not match resolution_deg: "
            f"expected {expected_rows}x{expected_cols}, got {grid.rows}x{grid.cols}"
        )
    expected_len = grid.rows * grid.cols
    if len(grid.values) != expected_len:
        raise ValueError(
            f"Grid values length {len(grid.values)} does not match "
            f"{grid.rows}x{grid.cols}={expected_len}"
        )


@lru_cache(maxsize=1)
def load_light_pollution_grid(path: str) -> LightPollutionGrid:
    """Load and validate the committed World Atlas grid JSON artifact."""
    resolved = resolve_grid_path(path)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    grid = LightPollutionGrid(
        source=str(payload["source"]),
        resolution_deg=float(payload["resolution_deg"]),
        west=float(payload["west"]),
        south=float(payload["south"]),
        rows=int(payload["rows"]),
        cols=int(payload["cols"]),
        nodata=float(payload["nodata"]),
        values=tuple(float(value) for value in payload["values"]),
    )
    _validate_grid_metadata(grid)
    return grid


def _grid_value(grid: LightPollutionGrid, row: int, col: int) -> float:
    return grid.values[row * grid.cols + col]


def _is_missing_value(grid: LightPollutionGrid, value: float) -> bool:
    return value < 0 or math.isclose(value, grid.nodata, rel_tol=0.0, abs_tol=1e-9)


def sample_artificial_brightness(
    latitude: float,
    longitude: float,
    grid: LightPollutionGrid,
) -> float | None:
    """Bilinear sample artificial radiance (mcd/m²); None when data is missing."""
    col_fraction = (longitude - grid.west) / grid.resolution_deg
    row_fraction = (latitude - grid.south) / grid.resolution_deg
    col_fraction = max(0.0, min(col_fraction, grid.cols - 1))
    row_fraction = max(0.0, min(row_fraction, grid.rows - 1))

    col_0 = int(math.floor(col_fraction))
    row_0 = int(math.floor(row_fraction))
    col_1 = min(col_0 + 1, grid.cols - 1)
    row_1 = min(row_0 + 1, grid.rows - 1)

    corners = (
        _grid_value(grid, row_0, col_0),
        _grid_value(grid, row_0, col_1),
        _grid_value(grid, row_1, col_0),
        _grid_value(grid, row_1, col_1),
    )
    if any(_is_missing_value(grid, value) for value in corners):
        return None

    col_weight = col_fraction - col_0
    row_weight = row_fraction - row_0
    top = corners[0] * (1.0 - col_weight) + corners[1] * col_weight
    bottom = corners[2] * (1.0 - col_weight) + corners[3] * col_weight
    sampled = top * (1.0 - row_weight) + bottom * row_weight
    if _is_missing_value(grid, sampled):
        return None
    return sampled


def _build_site_conditions(artificial_brightness: float) -> SiteSkyConditions:
    sqm = artificial_brightness_to_sqm(artificial_brightness)
    return SiteSkyConditions(
        bortle=sqm_to_bortle(sqm),
        sqm=sqm,
        limiting_magnitude=sqm_to_nelm(sqm),
        source=GRID_SOURCE,
    )


def lookup_site_darkness(
    latitude: float,
    longitude: float,
    *,
    grid_path: str,
) -> SiteSkyConditions:
    """Return site Bortle/SQM/NELM for coordinates, with cache and fallback."""
    key = _cache_key(latitude, longitude)
    cached = _CACHE.get(key)
    now = time.monotonic()
    if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        grid = load_light_pollution_grid(grid_path)
        artificial = sample_artificial_brightness(latitude, longitude, grid)
        if artificial is None:
            logger.warning("Light pollution grid missing data for %s", key)
            return FALLBACK_SITE
        site = _build_site_conditions(artificial)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("Light pollution lookup failed for %s: %s", key, exc)
        return FALLBACK_SITE

    _CACHE[key] = (now, site)
    return site


def clear_light_pollution_caches() -> None:
    """Clear lookup and grid caches (for tests)."""
    _CACHE.clear()
    load_light_pollution_grid.cache_clear()

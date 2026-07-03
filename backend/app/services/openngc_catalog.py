"""OpenNGC catalog loader for deep sky object visibility."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

OBSERVABLE_DSO_TYPES = frozenset(
    {
        "G",
        "GPair",
        "GTrpl",
        "GGroup",
        "GCl",
        "OCl",
        "Cl+N",
        "PN",
        "EmN",
        "Neb",
        "RfN",
        "HII",
        "SNR",
    }
)

EXCLUDED_TYPES = frozenset({"*", "**", "NonEx", "Dup", "Nova", "Other"})

OPENNGC_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "openngc" / "NGC.csv"
)

_RA_PATTERN = re.compile(r"^(\d+):(\d+):([\d.]+)$")
_DEC_PATTERN = re.compile(r"^([+-])(\d+):(\d+):([\d.]+)$")


@dataclass(frozen=True, slots=True)
class DsoCatalogEntry:
    """Parsed deep sky object from OpenNGC."""

    name: str
    object_type: str
    ra_hours: float
    dec_deg: float
    v_mag: float | None
    b_mag: float | None
    surf_br: float | None
    common_name: str | None
    messier: int | None


def _parse_float(value: str | None) -> float | None:
    stripped = (value or "").strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    stripped = (value or "").strip()
    if not stripped:
        return None
    try:
        return int(float(stripped))
    except ValueError:
        return None


def parse_ra_hours(ra: str) -> float:
    """Convert OpenNGC RA string (HH:MM:SS.SS) to decimal hours."""
    match = _RA_PATTERN.match(ra.strip())
    if not match:
        raise ValueError(f"Invalid RA format: {ra!r}")
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours + minutes / 60.0 + seconds / 3600.0


def parse_dec_deg(dec: str) -> float:
    """Convert OpenNGC Dec string (+/-DD:MM:SS.SS) to decimal degrees."""
    match = _DEC_PATTERN.match(dec.strip())
    if not match:
        raise ValueError(f"Invalid Dec format: {dec!r}")
    sign = 1 if match.group(1) == "+" else -1
    degrees = int(match.group(2))
    minutes = int(match.group(3))
    seconds = float(match.group(4))
    return sign * (degrees + minutes / 60.0 + seconds / 3600.0)


def _first_common_name(raw: str | None) -> str | None:
    stripped = (raw or "").strip()
    if not stripped:
        return None
    return stripped.split(",")[0].strip() or None


def parse_openngc_row(row: dict[str, str]) -> DsoCatalogEntry | None:
    """Parse one OpenNGC CSV row; return None for excluded or invalid entries."""
    object_type = row.get("Type", "").strip()
    if object_type in EXCLUDED_TYPES or object_type not in OBSERVABLE_DSO_TYPES:
        return None

    v_mag = _parse_float(row.get("V-Mag", ""))
    b_mag = _parse_float(row.get("B-Mag", ""))
    if v_mag is None and b_mag is None:
        return None

    name = row.get("Name", "").strip()
    if not name:
        return None

    try:
        ra_hours = parse_ra_hours(row.get("RA", ""))
        dec_deg = parse_dec_deg(row.get("Dec", ""))
    except ValueError:
        return None

    return DsoCatalogEntry(
        name=name,
        object_type=object_type,
        ra_hours=ra_hours,
        dec_deg=dec_deg,
        v_mag=v_mag,
        b_mag=b_mag,
        surf_br=_parse_float(row.get("SurfBr", "")),
        common_name=_first_common_name(row.get("Common names", "")),
        messier=_parse_int(row.get("M", "")),
    )


def load_openngc_catalog_from_path(path: Path) -> tuple[DsoCatalogEntry, ...]:
    """Load and filter OpenNGC catalog from a CSV file path."""
    if not path.exists():
        return ()

    entries: list[DsoCatalogEntry] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            entry = parse_openngc_row(row)
            if entry is not None:
                entries.append(entry)
    return tuple(entries)


@lru_cache(maxsize=1)
def load_openngc_catalog() -> tuple[DsoCatalogEntry, ...]:
    """Load the bundled OpenNGC catalog (cached)."""
    return load_openngc_catalog_from_path(OPENNGC_CATALOG_PATH)


def best_magnitude(entry: DsoCatalogEntry) -> float:
    """Return the best available visual magnitude for an object."""
    if entry.v_mag is not None:
        return entry.v_mag
    if entry.b_mag is not None:
        return entry.b_mag
    raise ValueError(f"Catalog entry {entry.name} has no magnitude")


def max_altitude_at_latitude(dec_deg: float, latitude: float) -> float:
    """Return maximum possible altitude for a fixed declination at a latitude."""
    return 90.0 - abs(latitude - dec_deg)

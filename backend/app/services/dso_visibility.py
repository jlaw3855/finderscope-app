"""Deep sky object visibility ranking and timeline windows."""

from __future__ import annotations

from dataclasses import dataclass

from astronomy import Body, Horizon, Illumination, Observer, Refraction, Time

from app.models.dso_visibility import DsoDayVisibility, DsoVisibilityRow, SiteSkyConditions
from app.services.astronomy_time import calendar_day_bounds, time_to_local_hhmm
from app.services.moon_position import effective_moon_illumination
from app.services.openngc_catalog import (
    DsoCatalogEntry,
    best_magnitude,
    load_openngc_catalog,
    max_altitude_at_latitude,
)
from app.services.visibility_windows import (
    ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG,
    SAMPLE_INTERVAL_MINUTES,
    collect_sun_below_windows,
    intersect_windows,
    merge_time_windows,
    to_visibility_windows,
)

MOON_PENALTY_MAX = 4.0
MAGNITUDE_PREFILTER_BUFFER = 3.0
SURFACE_BRIGHTNESS_CONTRAST_OFFSET = 5.0
ALTITUDE_BONUS_FACTOR = 0.02
TOP_OBJECT_COUNT = 10


@dataclass(frozen=True, slots=True)
class _ScoredDso:
    entry: DsoCatalogEntry
    row: DsoVisibilityRow
    score: float


def fixed_object_altitude(
    observer: Observer,
    ra_hours: float,
    dec_deg: float,
    moment: Time,
) -> float:
    horizon = Horizon(moment, observer, ra_hours, dec_deg, Refraction.Normal)
    return horizon.altitude


def _collect_fixed_above_horizon_windows(
    observer: Observer,
    ra_hours: float,
    dec_deg: float,
    day_start: Time,
    day_end: Time,
) -> list[tuple[Time, Time]]:
    step_days = SAMPLE_INTERVAL_MINUTES / (24.0 * 60.0)
    samples: list[tuple[Time, float]] = []
    sample = day_start
    while sample.ut <= day_end.ut:
        alt = fixed_object_altitude(observer, ra_hours, dec_deg, sample)
        samples.append((sample, alt))
        sample = Time.AddDays(sample, step_days)

    if not samples:
        return []

    windows: list[tuple[Time, Time]] = []
    index = 0
    while index < len(samples):
        _, alt = samples[index]
        if alt <= 0:
            index += 1
            continue

        start_time = samples[index][0]
        end_time = start_time
        index += 1
        while index < len(samples) and samples[index][1] > 0:
            end_time = samples[index][0]
            index += 1
        if index < len(samples):
            windows.append((start_time, end_time))
        else:
            windows.append((start_time, day_end))
            break

    return windows


def _moon_phase_pct_at(observer: Observer, moment: Time) -> float:
    illumination = Illumination(Body.Moon, moment)
    return max(0.0, min(100.0, illumination.phase_fraction * 100.0))


def _effective_limiting_magnitude(
    site: SiteSkyConditions,
    observer: Observer,
    moment: Time,
) -> float:
    from app.services.astronomy_geometry import altitude_deg

    phase_pct = _moon_phase_pct_at(observer, moment)
    moon_alt = altitude_deg(Body.Moon, observer, moment)
    moon_eff = effective_moon_illumination(phase_pct, moon_alt)
    moon_penalty = (moon_eff / 100.0) * MOON_PENALTY_MAX
    return site.limiting_magnitude - moon_penalty


def _surface_brightness_penalty(entry: DsoCatalogEntry, site_sqm: float) -> float:
    if entry.surf_br is None:
        return 0.0
    return max(0.0, entry.surf_br - site_sqm + SURFACE_BRIGHTNESS_CONTRAST_OFFSET)


def _peak_within_windows(
    observer: Observer,
    ra_hours: float,
    dec_deg: float,
    windows: list[tuple[Time, Time]],
    timezone_name: str,
) -> tuple[float | None, str | None, Time | None]:
    if not windows:
        return None, None, None

    best_alt = None
    best_time: Time | None = None
    step_days = SAMPLE_INTERVAL_MINUTES / (24.0 * 60.0)

    for window_start, window_end in windows:
        sample = window_start
        while sample.ut <= window_end.ut:
            alt = fixed_object_altitude(observer, ra_hours, dec_deg, sample)
            if best_alt is None or alt > best_alt:
                best_alt = alt
                best_time = sample
            sample = Time.AddDays(sample, step_days)

    if best_time is None or best_alt is None:
        return None, None, None

    return round(best_alt, 1), time_to_local_hhmm(best_time, timezone_name), best_time


def _visibility_score(
    entry: DsoCatalogEntry,
    site: SiteSkyConditions,
    observer: Observer,
    peak_time: Time,
    peak_alt: float,
) -> tuple[float, float]:
    obj_mag = best_magnitude(entry)
    effective_nelm = _effective_limiting_magnitude(site, observer, peak_time)
    contrast = effective_nelm - obj_mag - _surface_brightness_penalty(entry, site.sqm)
    alt_bonus = peak_alt * ALTITUDE_BONUS_FACTOR
    return contrast, contrast + alt_bonus


def _candidate_entries(
    latitude: float,
    site: SiteSkyConditions,
    catalog: tuple[DsoCatalogEntry, ...],
) -> list[DsoCatalogEntry]:
    mag_cutoff = site.limiting_magnitude + MAGNITUDE_PREFILTER_BUFFER
    candidates: list[DsoCatalogEntry] = []
    for entry in catalog:
        if max_altitude_at_latitude(entry.dec_deg, latitude) <= 0:
            continue
        if best_magnitude(entry) > mag_cutoff:
            continue
        candidates.append(entry)
    return candidates


def _visibility_row(
    entry: DsoCatalogEntry,
    observer: Observer,
    day_start: Time,
    day_end: Time,
    timezone_name: str,
    site: SiteSkyConditions,
    *,
    astronomical_sun_windows: list[tuple[Time, Time]],
) -> _ScoredDso | None:
    horizon_windows = _collect_fixed_above_horizon_windows(
        observer,
        entry.ra_hours,
        entry.dec_deg,
        day_start,
        day_end,
    )
    astronomical_windows = merge_time_windows(
        intersect_windows(horizon_windows, astronomical_sun_windows)
    )

    peak_alt, peak_at, peak_time = _peak_within_windows(
        observer,
        entry.ra_hours,
        entry.dec_deg,
        astronomical_windows,
        timezone_name,
    )
    if peak_alt is None or peak_time is None:
        return None

    contrast, score = _visibility_score(entry, site, observer, peak_time, peak_alt)
    if contrast <= 0:
        return None

    row = DsoVisibilityRow(
        id=entry.name,
        name=entry.name,
        common_name=entry.common_name,
        object_type=entry.object_type,
        visible=len(astronomical_windows) > 0,
        windows_astronomical=to_visibility_windows(astronomical_windows, timezone_name),
        peak_altitude_deg=peak_alt,
        peak_at=peak_at,
        magnitude=round(best_magnitude(entry), 1),
        contrast=round(contrast, 2),
        visibility_score=round(score, 2),
    )
    return _ScoredDso(entry=entry, row=row, score=score)


def compute_dso_visibility(
    latitude: float,
    longitude: float,
    timezone_name: str,
    dates: list[str],
    site: SiteSkyConditions,
    *,
    catalog: tuple[DsoCatalogEntry, ...] | None = None,
) -> list[DsoDayVisibility]:
    observer = Observer(latitude, longitude, 0.0)
    entries = catalog if catalog is not None else load_openngc_catalog()
    candidates = _candidate_entries(latitude, site, entries)

    results: list[DsoDayVisibility] = []
    for date_str in dates:
        day_start, day_end = calendar_day_bounds(date_str, timezone_name)
        astronomical_sun_windows = collect_sun_below_windows(
            observer, day_start, day_end, ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG
        )

        scored: list[_ScoredDso] = []
        for entry in candidates:
            result = _visibility_row(
                entry,
                observer,
                day_start,
                day_end,
                timezone_name,
                site,
                astronomical_sun_windows=astronomical_sun_windows,
            )
            if result is not None:
                scored.append(result)

        scored.sort(
            key=lambda item: (
                -item.score,
                best_magnitude(item.entry),
                -(item.row.peak_altitude_deg or 0.0),
            )
        )
        top_rows = [item.row for item in scored[:TOP_OBJECT_COUNT]]
        results.append(DsoDayVisibility(date=date_str, objects=top_rows))

    return results

"""Planet above-horizon visibility for forecast calendar days."""

from __future__ import annotations

from astronomy import Body, Illumination, Observer, Time

from app.models.astronomy import PlanetDayVisibility, PlanetVisibilityRow
from app.services.astronomy_geometry import altitude_deg
from app.services.astronomy_time import calendar_day_bounds, time_to_local_hhmm
from app.services.planet_phenomena import (
    compute_jupiter_moons,
    compute_saturn_ring_tilt,
)
from app.services.rise_set import collect_above_horizon_windows
from app.services.visibility_windows import (
    ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG,
    CIVIL_TWILIGHT_SUN_ALTITUDE_DEG,
    SAMPLE_INTERVAL_MINUTES,
    collect_sun_below_windows,
    intersect_windows,
    merge_time_windows,
    to_visibility_windows,
)

NAKED_EYE_BODIES: list[tuple[Body, str]] = [
    (Body.Mercury, "Mercury"),
    (Body.Venus, "Venus"),
    (Body.Mars, "Mars"),
    (Body.Jupiter, "Jupiter"),
    (Body.Saturn, "Saturn"),
]

TELESCOPE_BODIES: list[tuple[Body, str]] = [
    (Body.Uranus, "Uranus"),
    (Body.Neptune, "Neptune"),
]


def _peak_within_windows(
    body: Body,
    observer: Observer,
    windows: list[tuple[Time, Time]],
    timezone_name: str,
) -> tuple[float | None, str | None, float | None]:
    if not windows:
        return None, None, None

    best_alt = None
    best_time: Time | None = None
    step_days = SAMPLE_INTERVAL_MINUTES / (24.0 * 60.0)

    for window_start, window_end in windows:
        sample = window_start
        while sample.ut <= window_end.ut:
            alt = altitude_deg(body, observer, sample)
            if best_alt is None or alt > best_alt:
                best_alt = alt
                best_time = sample
            sample = Time.AddDays(sample, step_days)

    if best_time is None or best_alt is None:
        return None, None, None

    magnitude = round(Illumination(body, best_time).mag, 1)
    return round(best_alt, 1), time_to_local_hhmm(best_time, timezone_name), magnitude


def _visibility_row(
    body: Body,
    label: str,
    observer: Observer,
    day_start: Time,
    day_end: Time,
    timezone_name: str,
    *,
    civil_sun_windows: list[tuple[Time, Time]],
    astronomical_sun_windows: list[tuple[Time, Time]],
) -> PlanetVisibilityRow:
    horizon_windows = collect_above_horizon_windows(body, observer, day_start, day_end)

    civil_windows = merge_time_windows(intersect_windows(horizon_windows, civil_sun_windows))
    astronomical_windows = merge_time_windows(
        intersect_windows(horizon_windows, astronomical_sun_windows)
    )

    peak_windows = astronomical_windows or civil_windows
    peak_alt, peak_at, magnitude = _peak_within_windows(
        body, observer, peak_windows, timezone_name
    )

    return PlanetVisibilityRow(
        body=label,
        visible=len(civil_windows) > 0,
        windows_civil=to_visibility_windows(civil_windows, timezone_name),
        windows_astronomical=to_visibility_windows(astronomical_windows, timezone_name),
        peak_altitude_deg=peak_alt,
        peak_at=peak_at,
        magnitude=magnitude,
    )


def _attach_planet_phenomena(
    row: PlanetVisibilityRow,
    observer: Observer,
    date_str: str,
    timezone_name: str,
) -> PlanetVisibilityRow:
    if not row.visible or not row.peak_at:
        return row

    updates: dict[str, object] = {}
    if row.body == "Jupiter":
        jupiter_moons = compute_jupiter_moons(observer, date_str, row.peak_at, timezone_name)
        if jupiter_moons is not None:
            updates["jupiter_moons"] = jupiter_moons
    elif row.body == "Saturn":
        ring_tilt, ring_note = compute_saturn_ring_tilt(
            observer,
            date_str,
            row.peak_at,
            timezone_name,
        )
        if ring_tilt is not None:
            updates["saturn_ring_tilt_deg"] = ring_tilt
            updates["saturn_ring_note"] = ring_note

    if not updates:
        return row
    return row.model_copy(update=updates)


def compute_planet_visibility(
    latitude: float,
    longitude: float,
    timezone_name: str,
    dates: list[str],
    *,
    include_telescope_bodies: bool = True,
) -> list[PlanetDayVisibility]:
    observer = Observer(latitude, longitude, 0.0)
    bodies = list(NAKED_EYE_BODIES)
    if include_telescope_bodies:
        bodies.extend(TELESCOPE_BODIES)

    results: list[PlanetDayVisibility] = []
    for date_str in dates:
        day_start, day_end = calendar_day_bounds(date_str, timezone_name)
        civil_sun_windows = collect_sun_below_windows(
            observer, day_start, day_end, CIVIL_TWILIGHT_SUN_ALTITUDE_DEG
        )
        astronomical_sun_windows = collect_sun_below_windows(
            observer, day_start, day_end, ASTRONOMICAL_TWILIGHT_SUN_ALTITUDE_DEG
        )
        planets = [
            _attach_planet_phenomena(
                _visibility_row(
                    body,
                    label,
                    observer,
                    day_start,
                    day_end,
                    timezone_name,
                    civil_sun_windows=civil_sun_windows,
                    astronomical_sun_windows=astronomical_sun_windows,
                ),
                observer,
                date_str,
                timezone_name,
            )
            for body, label in bodies
        ]
        results.append(PlanetDayVisibility(date=date_str, planets=planets))
    return results

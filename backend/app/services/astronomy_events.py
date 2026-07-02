"""Search upcoming astronomical events using astronomy-engine."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime

import astronomy
from astronomy import (
    Body,
    EclipseKind,
    Equator,
    Horizon,
    Observer,
    Refraction,
    SearchLocalSolarEclipse,
    SearchLunarEclipse,
    SearchRelativeLongitude,
    SearchTransit,
    Time,
)

from app.models.astronomy import AstronomyEvent
from app.services.astronomy_time import (
    local_datetime_to_time,
    time_to_utc_datetime,
    utc_now_time,
)
from app.services.meteor_showers import (
    load_meteor_shower_catalog,
    radiant_altitude,
    sun_below_astronomical_twilight,
)

EVENT_WINDOW_DAYS = 90
PLANET_CONJUNCTION_MAX_SEPARATION_DEG = 3.0
PLANET_CONJUNCTION_PAIRS: list[tuple[Body, Body, str]] = [
    (Body.Venus, Body.Jupiter, "Venus and Jupiter"),
    (Body.Mars, Body.Saturn, "Mars and Saturn"),
    (Body.Jupiter, Body.Saturn, "Jupiter and Saturn"),
    (Body.Mercury, Body.Venus, "Mercury and Venus"),
    (Body.Mars, Body.Jupiter, "Mars and Jupiter"),
]

OPPOSITION_BODIES: list[tuple[Body, str]] = [
    (Body.Mars, "Mars"),
    (Body.Jupiter, "Jupiter"),
    (Body.Saturn, "Saturn"),
    (Body.Uranus, "Uranus"),
    (Body.Neptune, "Neptune"),
]

INFERIOR_SUPERIOR_BODIES: list[tuple[Body, str]] = [
    (Body.Mercury, "Mercury"),
    (Body.Venus, "Venus"),
]


def _event_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return digest[:16]


def _utc_dt(value: Time | None) -> datetime | None:
    if value is None:
        return None
    return time_to_utc_datetime(value)


def _require_utc_dt(value: Time | None) -> datetime:
    if value is None:
        raise ValueError("Expected astronomy Time value.")
    return time_to_utc_datetime(value)


def _minutes_from_peak(peak: Time, minutes: float) -> Time:
    return Time.AddDays(peak, minutes / (24.0 * 60.0))


def _lunar_eclipse_kind_label(kind: EclipseKind) -> str:
    if kind == EclipseKind.Penumbral:
        return "penumbral lunar eclipse"
    if kind == EclipseKind.Partial:
        return "partial lunar eclipse"
    if kind == EclipseKind.Total:
        return "total lunar eclipse"
    return "lunar eclipse"


def _solar_eclipse_kind_label(kind: EclipseKind) -> str:
    if kind == EclipseKind.Partial:
        return "partial solar eclipse"
    if kind == EclipseKind.Annular:
        return "annular solar eclipse"
    if kind == EclipseKind.Total:
        return "total solar eclipse"
    return "solar eclipse"


def _collect_lunar_eclipses(start: Time, end: Time) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    cursor = start
    while cursor.ut < end.ut:
        info = SearchLunarEclipse(cursor)
        peak = info.peak
        if peak.ut >= end.ut:
            break
        kind_label = _lunar_eclipse_kind_label(info.kind)
        start = _minutes_from_peak(peak, -info.sd_penum)
        end = _minutes_from_peak(peak, info.sd_penum)
        peak_dt = _require_utc_dt(peak)
        events.append(
            AstronomyEvent(
                id=_event_id("lunar_eclipse", str(peak.ut)),
                category="lunar_eclipse",
                title=f"{kind_label.title()}",
                start_at=_require_utc_dt(start),
                peak_at=peak_dt,
                end_at=_require_utc_dt(end),
                description=(
                    f"{kind_label.capitalize()} with peak at "
                    f"{peak_dt.strftime('%Y-%m-%d %H:%M UTC')}."
                ),
                visible_locally=True,
            )
        )
        cursor = Time.AddDays(peak, 0.01)
    return events


def _collect_local_solar_eclipses(
    start: Time, end: Time, observer: Observer
) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    cursor = start
    while cursor.ut < end.ut:
        info = SearchLocalSolarEclipse(cursor, observer)
        peak = info.peak.time
        if peak.ut >= end.ut:
            break
        if info.peak.altitude <= 0:
            cursor = Time.AddDays(peak, 0.01)
            continue
        kind_label = _solar_eclipse_kind_label(info.kind)
        events.append(
            AstronomyEvent(
                id=_event_id("solar_eclipse", str(peak.ut)),
                category="solar_eclipse",
                title=f"{kind_label.title()}",
                start_at=_require_utc_dt(info.partial_begin.time),
                peak_at=_require_utc_dt(peak),
                end_at=_require_utc_dt(info.partial_end.time),
                description=(
                    f"{kind_label.capitalize()} visible locally with peak altitude "
                    f"{info.peak.altitude:.1f}°."
                ),
                visible_locally=True,
            )
        )
        cursor = Time.AddDays(peak, 0.01)
    return events


def _collect_transits(start: Time, end: Time) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    for body, label in ((Body.Mercury, "Mercury"), (Body.Venus, "Venus")):
        cursor = start
        while cursor.ut < end.ut:
            info = SearchTransit(body, cursor)
            peak = info.peak
            if peak.ut >= end.ut:
                break
            events.append(
                AstronomyEvent(
                    id=_event_id("transit", label, str(peak.ut)),
                    category="transit",
                    title=f"{label} transit",
                    start_at=_require_utc_dt(info.start),
                    peak_at=_require_utc_dt(peak),
                    end_at=_require_utc_dt(info.finish),
                    description=(
                        f"{label} crosses the solar disk (global event; "
                        f"local visibility depends on Sun altitude)."
                    ),
                    visible_locally=False,
                )
            )
            cursor = Time.AddDays(peak, 0.01)
    return events


def _collect_sun_relative_events(start: Time, end: Time) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    for body, label in OPPOSITION_BODIES:
        cursor = start
        while cursor.ut < end.ut:
            peak = SearchRelativeLongitude(body, 0, cursor)
            if peak.ut >= end.ut:
                break
            events.append(
                AstronomyEvent(
                    id=_event_id("opposition", label, str(peak.ut)),
                    category="opposition",
                    title=f"{label} at opposition",
                    start_at=_require_utc_dt(peak),
                    peak_at=_require_utc_dt(peak),
                    end_at=None,
                    description=f"{label} is opposite the Sun in the sky.",
                    visible_locally=True,
                )
            )
            cursor = Time.AddDays(peak, 0.01)

    for body, label in INFERIOR_SUPERIOR_BODIES:
        for target, phase in ((0, "inferior conjunction"), (180, "superior conjunction")):
            cursor = start
            while cursor.ut < end.ut:
                peak = SearchRelativeLongitude(body, target, cursor)
                if peak.ut >= end.ut:
                    break
                events.append(
                    AstronomyEvent(
                        id=_event_id("conjunction", label, phase, str(peak.ut)),
                        category="conjunction",
                        title=f"{label} {phase}",
                        start_at=_require_utc_dt(peak),
                        peak_at=_require_utc_dt(peak),
                        end_at=None,
                        description=f"{label} reaches {phase} with the Sun.",
                        visible_locally=False,
                    )
                )
                cursor = Time.AddDays(peak, 0.01)
    return events


def _collect_planet_conjunctions(start: Time, end: Time) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    step_hours = 6
    total_hours = EVENT_WINDOW_DAYS * 24

    for body1, body2, label in PLANET_CONJUNCTION_PAIRS:
        best_time: Time | None = None
        best_sep = 999.0
        hour = 0
        while hour <= total_hours:
            sample = Time.AddDays(start, hour / 24.0)
            if sample.ut >= end.ut:
                break
            sep = astronomy.PairLongitude(body1, body2, sample)
            if sep <= PLANET_CONJUNCTION_MAX_SEPARATION_DEG and sep < best_sep:
                best_sep = sep
                best_time = sample
            hour += step_hours

        if best_time is None:
            continue

        # Refine closest approach within ±12 hours of the coarse minimum.
        refine_start = Time.AddDays(best_time, -0.5)
        refine_end = Time.AddDays(best_time, 0.5)
        refined = best_time
        refined_sep = best_sep
        refine_hour = 0
        while refine_hour <= 24:
            sample = Time.AddDays(refine_start, refine_hour / 24.0)
            if sample.ut > refine_end.ut:
                break
            sep = astronomy.PairLongitude(body1, body2, sample)
            if sep < refined_sep:
                refined_sep = sep
                refined = sample
            refine_hour += 1

        if refined_sep > PLANET_CONJUNCTION_MAX_SEPARATION_DEG:
            continue

        events.append(
            AstronomyEvent(
                id=_event_id("conjunction", label, str(refined.ut)),
                category="conjunction",
                title=f"{label} conjunction",
                start_at=_require_utc_dt(refined),
                peak_at=_require_utc_dt(refined),
                end_at=None,
                description=(
                    f"{label} appear within {refined_sep:.1f}° separation."
                ),
                visible_locally=True,
            )
        )
    return events


def _dedupe_events(events: list[AstronomyEvent]) -> list[AstronomyEvent]:
    seen: set[str] = set()
    unique: list[AstronomyEvent] = []
    for event in sorted(events, key=lambda item: item.start_at):
        if event.id in seen:
            continue
        seen.add(event.id)
        unique.append(event)
    return unique


def _load_meteor_shower_catalog() -> list[dict]:
    return list(load_meteor_shower_catalog())


def _altitude_deg(body: Body, observer: Observer, moment: Time) -> float:
    equator = Equator(body, moment, observer, ofdate=True, aberration=True)
    horizon = Horizon(moment, observer, equator.ra, equator.dec, Refraction.Normal)
    return horizon.altitude


def _radiant_altitude(
    observer: Observer,
    ra_hours: float,
    dec_deg: float,
    moment: Time,
) -> float:
    return radiant_altitude(observer, ra_hours, dec_deg, moment)


def _sun_below_astronomical_twilight(observer: Observer, moment: Time) -> bool:
    return sun_below_astronomical_twilight(observer, moment)


def _years_in_window(start: Time, end: Time) -> list[int]:
    start_year = time_to_utc_datetime(start).year
    end_year = time_to_utc_datetime(end).year
    return list(range(start_year, end_year + 1))


def _collect_meteor_showers(
    start: Time,
    end: Time,
    observer: Observer,
) -> list[AstronomyEvent]:
    events: list[AstronomyEvent] = []
    for shower in _load_meteor_shower_catalog():
        for year in _years_in_window(start, end):
            peak_date = date(year, shower["peak_month"], shower["peak_day"])
            peak_dt = datetime(peak_date.year, peak_date.month, peak_date.day, 5, 0, tzinfo=UTC)
            peak_time = local_datetime_to_time(peak_dt)
            if peak_time.ut < start.ut or peak_time.ut >= end.ut:
                continue

            radiant_alt = _radiant_altitude(
                observer,
                shower["radiant_ra_hours"],
                shower["radiant_dec_deg"],
                peak_time,
            )
            visible_locally = radiant_alt > 0 and _sun_below_astronomical_twilight(observer, peak_time)
            peak_utc = time_to_utc_datetime(peak_time)
            zhr = shower.get("zhr_nominal")
            zhr_text = f" Nominal ZHR ~{zhr}." if zhr is not None else ""
            constellation = shower.get("constellation")
            title = shower["name"]
            if constellation:
                title = f"{shower['name']} ({constellation})"

            events.append(
                AstronomyEvent(
                    id=_event_id("meteor_shower", shower["id"], str(peak_time.ut)),
                    category="meteor_shower",
                    title=title,
                    start_at=peak_utc,
                    peak_at=peak_utc,
                    end_at=None,
                    description=(
                        f"Peak activity around {peak_date.isoformat()} with radiant altitude "
                        f"{radiant_alt:.1f}° at sample time.{zhr_text}"
                    ),
                    visible_locally=visible_locally,
                )
            )
    return events


def search_astronomy_events(
    latitude: float,
    longitude: float,
    *,
    start_time: Time | None = None,
    window_days: int = EVENT_WINDOW_DAYS,
) -> list[AstronomyEvent]:
    """Return upcoming astronomy events within the search window."""
    start = start_time or utc_now_time()
    end = Time.AddDays(start, float(window_days))
    observer = Observer(latitude, longitude, 0.0)

    events: list[AstronomyEvent] = []
    events.extend(_collect_lunar_eclipses(start, end))
    events.extend(_collect_local_solar_eclipses(start, end, observer))
    events.extend(_collect_transits(start, end))
    events.extend(_collect_sun_relative_events(start, end))
    events.extend(_collect_planet_conjunctions(start, end))
    events.extend(_collect_meteor_showers(start, end, observer))

    return _dedupe_events(events)

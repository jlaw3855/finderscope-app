"""Generate E2E JSON fixtures from backend scoring fixtures."""

import copy
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from app.services.scoring import build_forecast

FIXTURES_DIR = Path(__file__).parent
REPO_ROOT = FIXTURES_DIR.parents[2]
E2E_FIXTURES_DIR = REPO_ROOT / "e2e" / "fixtures"
WEATHER_BASE_DATE = date(2025, 6, 20)


def _load(name: str) -> dict:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _shift_weather_dates(weather_data: dict, forecast_start: date) -> dict:
    delta_days = (forecast_start - WEATHER_BASE_DATE).days
    if delta_days == 0:
        return weather_data

    shifted = copy.deepcopy(weather_data)

    def shift_token(value: str) -> str:
        if "T" in value:
            shifted_dt = datetime.fromisoformat(value) + timedelta(days=delta_days)
            return shifted_dt.strftime("%Y-%m-%dT%H:%M")
        shifted_date = date.fromisoformat(value) + timedelta(days=delta_days)
        return shifted_date.isoformat()

    for block_name in ("hourly", "minutely_15", "daily"):
        block = shifted.get(block_name)
        if not isinstance(block, dict) or "time" not in block:
            continue
        block["time"] = [shift_token(entry) for entry in block["time"]]

    return shifted


def _extend_time_series(
    time_series: dict,
    nights: int = 7,
    *,
    start: date | None = None,
) -> tuple[dict, date, date]:
    base_days = time_series["astronomy"]
    if not base_days:
        raise ValueError("time_series fixture must include at least one astronomy day")

    start = start or date.fromisoformat(base_days[0]["date"])
    prior_template = base_days[0].copy()
    prior_template["date"] = (start - timedelta(days=1)).isoformat()

    extended = []
    for index in range(nights):
        template = base_days[index % len(base_days)].copy()
        template["date"] = (start + timedelta(days=index)).isoformat()
        extended.append(template)

    forecast_end = start + timedelta(days=nights - 1)
    astronomy = [prior_template, *extended]
    return {**time_series, "astronomy": astronomy}, start, forecast_end


def main() -> None:
    location_data = _load("location.json")
    forecast_start = date(2026, 8, 9)
    weather_data = _shift_weather_dates(_load("weather.json"), forecast_start)
    time_series_data, forecast_start, forecast_end = _extend_time_series(
        _load("time_series.json"),
        start=forecast_start,
    )

    forecast = build_forecast(
        location_data,
        time_series_data,
        weather_data,
        forecast_start=forecast_start,
        forecast_end=forecast_end,
    )

    E2E_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    forecast_path = E2E_FIXTURES_DIR / "forecast-response.json"
    forecast_path.write_text(json.dumps(forecast.model_dump(), indent=2), encoding="utf-8")

    moon_path = E2E_FIXTURES_DIR / "moon-enrichment-response.json"
    moon_template = json.loads((E2E_FIXTURES_DIR / "moon-enrichment-response.json").read_text(encoding="utf-8"))
    moon_entries = []
    for index, night in enumerate(forecast.nights):
        template = moon_template["entries"][index % len(moon_template["entries"])]
        moon_entries.append(
            {
                **template,
                "date": night.date,
                "visual_url": f"/api/moon/visual/{night.date}.svg?profile=dark",
            }
        )
    moon_path.write_text(
        json.dumps(
            {
                **moon_template,
                "entries": moon_entries,
                "cached_count": len(moon_entries),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    astronomy_path = E2E_FIXTURES_DIR / "astronomy-response.json"
    astronomy_template = json.loads(astronomy_path.read_text(encoding="utf-8"))
    astronomy_dates = [night.date for night in forecast.nights]
    shifted_planet_visibility = []
    for index, entry in enumerate(astronomy_template.get("planet_visibility", [])):
        shifted_planet_visibility.append(
            {
                **entry,
                "date": astronomy_dates[index % len(astronomy_dates)],
            }
        )
    astronomy_path.write_text(
        json.dumps(
            {
                **astronomy_template,
                "planet_visibility": shifted_planet_visibility,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {forecast_path} ({len(forecast.nights)} nights)")
    if forecast.prior_day_dark_window:
        print(
            "  prior_day_dark_window:",
            forecast.prior_day_dark_window.start,
            "→",
            forecast.prior_day_dark_window.end,
        )


if __name__ == "__main__":
    main()

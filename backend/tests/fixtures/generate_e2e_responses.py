"""Generate E2E JSON fixtures from backend scoring fixtures."""

import json
from datetime import date, timedelta
from pathlib import Path

from app.services.scoring import build_forecast

FIXTURES_DIR = Path(__file__).parent
REPO_ROOT = FIXTURES_DIR.parents[2]
E2E_FIXTURES_DIR = REPO_ROOT / "e2e" / "fixtures"


def _load(name: str) -> dict:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _extend_time_series(time_series: dict, nights: int = 7) -> dict:
    base_days = time_series["astronomy"]
    if not base_days:
        return time_series

    start = date.fromisoformat(base_days[0]["date"])
    extended = []
    for index in range(nights):
        template = base_days[index % len(base_days)].copy()
        template["date"] = (start + timedelta(days=index)).isoformat()
        extended.append(template)

    return {**time_series, "astronomy": extended}


def main() -> None:
    location_data = _load("location.json")
    weather_data = _load("weather.json")
    time_series_data = _extend_time_series(_load("time_series.json"))

    forecast = build_forecast(location_data, time_series_data, weather_data)

    E2E_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    forecast_path = E2E_FIXTURES_DIR / "forecast-response.json"
    forecast_path.write_text(json.dumps(forecast.model_dump(), indent=2), encoding="utf-8")

    star_chart_path = E2E_FIXTURES_DIR / "star-chart-response.json"
    if not star_chart_path.exists():
        star_chart_path.write_text(
            json.dumps(
                {
                    "image_url": "https://example.com/finderscope-test-chart.png",
                    "view_type": "area",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"Wrote {forecast_path} ({len(forecast.nights)} nights)")


if __name__ == "__main__":
    main()

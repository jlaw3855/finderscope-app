# Dev Setup Reference

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `IPGEOLOCATION_API_KEY` | (empty) | **Required** for live geocode and astronomy time series |
| `FREEASTRO_API_KEY` | (empty) | Optional moon phase SVG enrichment |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed browser origins for the API |
| `MOON_ENRICHMENT_ENABLED` | `true` | Enable moon enrichment routes |
| `FORECAST_CACHE_ENABLED` | `true` | SQLite cache for geocode, astronomy, weather |
| `FORECAST_GEOCODE_TTL_HOURS` | `720` | Geocode cache TTL (~30 days) |
| `FORECAST_ASTRONOMY_TTL_HOURS` | `24` | IPGeolocation astronomy cache TTL |
| `FORECAST_WEATHER_TTL_HOURS` | `3` | Open-Meteo cache TTL |
| `SEVENTIMER_ENABLED` | `true` | 7timer ASTRO seeing/transparency for sky quality scoring |
| `FORECAST_ASTRO_TTL_HOURS` | `3` | 7timer ASTRO cache TTL |
| `SEVENTIMER_ALTITUDE_CORRECTION` | `0` | 7timer `ac` param (0, 2, or 7) |
| `NASA_API_KEY` | `DEMO_KEY` | NASA Open API key for landing-page APOD |
| `NOCTUA_ENRICHMENT_ENABLED` | `false` | NoctuaSky catalog metadata on astronomy events |
| `NOCTUA_BASE_URL` | NoctuaSky API v1 | Skysources client base URL |

## Platform notes

| Platform | Notes |
|----------|--------|
| Windows | `tzdata` is installed via `requirements.txt` (`sys_platform == "win32"`) for `zoneinfo` |
| macOS / Linux | System timezone database is used; `tzdata` is skipped |

## Install locations

| Package | Directory | Lockfile |
|---------|-----------|----------|
| Backend (pip) | `backend/` | `requirements.txt`, `requirements-dev.txt` |
| Frontend (npm) | `frontend/` | `package-lock.json` |
| E2E (npm) | `e2e/` | `package-lock.json` |

## Related skills

- **run-dev** — start backend and frontend after setup
- **integrity-check** — run tests and build verification (not first-time install)

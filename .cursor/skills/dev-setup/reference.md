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
| Windows | `tzdata` is installed via `requirements.txt` (`sys_platform == "win32"`) for `zoneinfo`; save `backend/.env` as **UTF-8** (not UTF-16); CRLF line endings are auto-normalized |
| macOS / Linux | System timezone database is used; `tzdata` is skipped; `.env` is usually UTF-8 with LF line endings |

### Cross-platform `.env` troubleshooting

| Issue | Windows | macOS / Linux |
|-------|---------|---------------|
| `.env` encoding | Notepad may save UTF-16 — use VS Code/Cursor **Save with Encoding → UTF-8** | Usually UTF-8 already |
| Line endings | CRLF (`\r\n`) is common; keys are auto-stripped | LF; same auto-normalization |
| OS env override | User/System `IPGEOLOCATION_API_KEY` overrides `backend/.env` | Same precedence; less common |
| Timezone errors | Install deps so `tzdata` is present (`pip install -r requirements.txt`) | Uses system tzdata |

**Check key health (does not print the key):**

```bash
cd backend
python -c "from app.config import get_settings, describe_api_key_health, get_ipgeolocation_key_source; s=get_settings(); print(describe_api_key_health(s.ipgeolocation_api_key, source=get_ipgeolocation_key_source()))"
```

**Windows — remove a stale shell env var:**

```powershell
echo $env:IPGEOLOCATION_API_KEY
Remove-Item Env:IPGEOLOCATION_API_KEY   # current session only
```

**Direct API probe** (paste your key locally in the browser):  
`https://api.ipgeolocation.io/v3/astronomy?apiKey=YOUR_KEY&location=Denver,CO`

If key health looks clean but the API still returns 401, the issue is account/plan (Astronomy v3), not OS formatting. Restart the backend after editing `.env`.

## Install locations

| Package | Directory | Lockfile |
|---------|-----------|----------|
| Backend (pip) | `backend/` | `requirements.txt`, `requirements-dev.txt` |
| Frontend (npm) | `frontend/` | `package-lock.json` |
| E2E (npm) | `e2e/` | `package-lock.json` |

## Related skills

- **run-dev** — start backend and frontend after setup
- **integrity-check** — run tests and build verification (not first-time install)

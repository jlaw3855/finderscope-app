# Finderscope

A full-stack web app for stargazers. Enter an address to get a 7-day stargazing weather forecast and generate a custom star chart for any date and time.

## Application functionality

### Forecast search

1. The user enters a street address or place name.
2. The backend geocodes the location and fetches seven nights of astronomical darkness windows, moon data, and hourly weather.
3. The UI displays one **night card** per evening, each with an overall stargazing score, rating, moon details, cloud/precipitation summaries, and suggested best hours.
4. Selecting a night opens an **hourly scores panel** with per-hour bars, weather metrics, dew point chart, and effective moon sky glow.

### Stargazing score

Each hour during astronomical darkness receives a score from 0–100 based on:

| Factor | Weight | Source |
|--------|--------|--------|
| Cloud cover | 40% | Open-Meteo hourly |
| Visibility | 25% | Open-Meteo hourly |
| Moon sky glow | 25% | IPGeolocation phase + Skyfield altitude |
| Precipitation / weather code | 10% | Open-Meteo hourly |

The nightly card score is the average of hourly scores during darkness. **Best hours** are contiguous windows where hourly scores reach 70 or higher.

Moon impact uses two related concepts:

| Term | Meaning |
|------|---------|
| **Disk lit** | Lunar phase illumination — how much of the moon's disk is illuminated that night |
| **Avg moon sky glow** | Average effective sky brightness from moonlight during darkness; drives the nightly score |
| **Effective moon sky glow** (hourly) | Phase illumination scaled by moon altitude via `sin(altitude)`; low or below-horizon moons contribute less |

Moonrise and moonset on night cards are informational. Hourly scores compute moon altitude with Skyfield at each hour's midpoint. On first forecast run, Skyfield downloads a JPL ephemeris file (~16 MB) into `backend/data/ephemeris/`.

### Star chart generation

The star chart panel lets the user pick a night, time, and view type (all-sky or constellation). The backend calls AstronomyAPI.com and returns an image URL rendered in the browser.

### External services

| Service | Role | API key |
|---------|------|---------|
| [IPGeolocation.io](https://ipgeolocation.io) | Geocoding, twilight windows, moon phase/times | Required |
| [Open-Meteo](https://open-meteo.com) | Hourly and daily weather | None |
| [AstronomyAPI.com](https://www.astronomyapi.com) | Star chart images | Required |

API keys live in `backend/.env` only; the frontend never sees them.

## File architecture

```
finderscope/
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── main.py             # App entry, CORS, router registration, /health
│   │   ├── config.py           # Settings from environment (.env)
│   │   ├── models/
│   │   │   ├── forecast.py     # Pydantic schemas for forecast API
│   │   │   └── star_chart.py   # Pydantic schemas for star chart API
│   │   ├── routers/
│   │   │   ├── forecast.py     # POST /api/forecast orchestration
│   │   │   └── star_chart.py   # POST /api/star-chart
│   │   └── services/
│   │       ├── ipgeolocation.py    # Astronomy API client (geocode + time series)
│   │       ├── openmeteo.py        # Weather forecast client
│   │       ├── scoring.py          # Merge weather + astronomy into scores
│   │       ├── moon_position.py    # Skyfield moon altitude + sky-glow curve
│   │       └── astronomyapi.py     # Star chart image generation
│   ├── data/ephemeris/         # Cached JPL ephemeris (gitignored, auto-downloaded)
│   ├── tests/
│   │   ├── test_scoring.py     # Scoring and forecast assembly tests
│   │   ├── test_moon_position.py
│   │   ├── test_routes.py      # Route tests with mocked services
│   │   ├── test_integration_live.py  # Opt-in live API tests
│   │   └── fixtures/           # JSON fixtures + E2E fixture generator
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── App.tsx             # Main layout and state wiring
│   │   ├── main.tsx            # React entry point
│   │   ├── index.css           # Global styles
│   │   ├── components/
│   │   │   ├── AddressSearch.tsx
│   │   │   ├── NightForecastCard.tsx   # Daily night summary cards
│   │   │   ├── HourlyScoreChart.tsx    # Hourly bars + weather metrics
│   │   │   ├── StarChartPanel.tsx
│   │   │   ├── CloudBreakdown.tsx
│   │   │   ├── PrecipitationBreakdownView.tsx
│   │   │   ├── DewPointChart.tsx
│   │   │   └── ErrorBanner.tsx
│   │   ├── hooks/
│   │   │   ├── useForecast.ts  # Forecast fetch state
│   │   │   └── useStarChart.ts # Star chart fetch state
│   │   ├── lib/
│   │   │   ├── backend-client.ts   # Typed fetch wrappers for /api
│   │   │   └── weather-format.ts   # Display formatters
│   │   └── types/
│   │       ├── forecast.ts
│   │       └── star-chart.ts
│   └── vite.config.ts          # Dev server; proxies /api → localhost:8000
│
├── e2e/                        # Playwright browser tests
│   ├── tests/app.spec.ts
│   └── fixtures/               # Mocked API responses for offline E2E
│
├── scripts/
│   ├── check-integrity.sh      # Full test/lint/build harness
│   └── record-e2e-fixtures.sh  # Refresh E2E fixtures from live APIs
│
├── .github/workflows/ci.yml    # Runs check-integrity.sh on push/PR
└── .cursor/skills/integrity-check/  # Agent skill for running checks
```

### Request flow

```mermaid
flowchart LR
  subgraph frontend [Frontend]
    UI[React UI]
  end
  subgraph backend [Backend]
    ForecastRouter["/api/forecast"]
    Scoring[scoring.build_forecast]
    StarChartRouter["/api/star-chart"]
  end
  subgraph external [External APIs]
    IPGeo[IPGeolocation]
    OpenMeteo[Open-Meteo]
    AstroAPI[AstronomyAPI]
  end
  UI --> ForecastRouter
  ForecastRouter --> IPGeo
  ForecastRouter --> OpenMeteo
  ForecastRouter --> Scoring
  Scoring --> MoonPos[moon_position Skyfield]
  UI --> StarChartRouter
  StarChartRouter --> AstroAPI
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Free API keys from [IPGeolocation.io](https://ipgeolocation.io) and [AstronomyAPI.com](https://www.astronomyapi.com)

Open-Meteo requires no API key.

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Fill in credentials from provider dashboards (see Prerequisites)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173` and proxies `/api` requests to the backend.

## Development testing

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

### Frontend

```bash
cd frontend
npm install
npm run test:run
npm run lint
```

### E2E (Playwright)

```bash
cd e2e
npm install
npm run test:install   # first time only
npm run test
```

E2E tests mock `/api/forecast` and `/api/star-chart` in the browser — no backend or external APIs required.

## Integrity checks

Run the full integrity harness from the repository root after code changes:

```bash
chmod +x scripts/check-integrity.sh   # first time only
./scripts/check-integrity.sh
```

Fast mode (skips the Vite production build):

```bash
./scripts/check-integrity.sh --fast
```

Live backend integration (~4 paid external API calls; requires valid `backend/.env`):

```bash
./scripts/check-integrity.sh --live
```

The harness runs, in order:

1. Skyfield ephemeris prefetch
2. Backend unit and route tests (`pytest`, excludes `live`)
3. Frontend unit tests (`vitest`)
4. E2E browser tests (`playwright`, mocked APIs)
5. Frontend lint (`oxlint`)
6. TypeScript compile (`tsc -b`)
7. Production build (`vite build`) — skipped with `--fast`
8. Live backend integration — only with `--live`

| Mode | External API calls |
|------|-------------------|
| Default | 0 |
| `--live` | ~4 paid (2 IPGeolocation + 1 AstronomyAPI; Open-Meteo is free) |

Refresh E2E fixtures from live responses when API shapes change:

```bash
chmod +x scripts/record-e2e-fixtures.sh
./scripts/record-e2e-fixtures.sh
```

Regenerate mocked forecast fixtures from backend scoring fixtures (no API calls):

```bash
cd backend
PYTHONPATH=. python3 tests/fixtures/generate_e2e_responses.py
```

A project Cursor skill at `.cursor/skills/integrity-check/` instructs the agent to run these checks before completing coding tasks.

## Continuous integration

GitHub Actions runs `./scripts/check-integrity.sh` on every push and pull request to `main`.
Live API tests are not run in CI.

## API reference

| Endpoint | Description | External calls |
|----------|-------------|----------------|
| `GET /health` | Health check | 0 |
| `POST /api/forecast` | 7-day stargazing forecast for an address | 2 IPGeolocation + 1 Open-Meteo |
| `POST /api/star-chart` | Generate a star chart image URL | 1 AstronomyAPI |

# Finderscope

A full-stack web app for stargazers. Enter an address to get a 7-day stargazing weather forecast and a local astronomy summary for your location.

## Application functionality

### Forecast search

1. The user enters a street address or place name.
2. The backend geocodes the location and fetches seven nights of astronomical darkness windows, moon data, and weather at hourly and 15-minutely resolution.
3. The UI displays one **night card** per evening, each with an overall stargazing score, rating, moon details, cloud/precipitation summaries, and suggested best hours.
4. Selecting a night opens a **scores panel** with half-hour (or hourly) bars during darkness, weather metrics, a dew point curve, and per-interval moon sky glow and altitude rows.

The scores panel uses a **unified left-aligned grid**: each row pairs a sticky label column with a data column so time labels, score bars, dew/air temperature lines, and metric values stay vertically aligned. Score values appear at the bottom of each bar; the dew point chart plots dew point and air temperature on a shared scale with padded Y-axis headroom. When `score_step_minutes` is `30`, columns are narrower and time labels are thinned to keep the panel readable.

### Stargazing score

Each score interval during astronomical darkness receives a score from 0–100 based on:

| Factor | Weight | Source |
|--------|--------|--------|
| Cloud cover | 40% | Open-Meteo (15-min preferred, hourly fallback) |
| Visibility | 25% | Open-Meteo (15-min preferred, hourly fallback) |
| Moon sky glow | 25% | IPGeolocation phase + Skyfield altitude |
| Precipitation / weather code | 10% | Open-Meteo (15-min preferred, hourly fallback) |

**Score step:** The API returns `score_step_minutes: 30` when half-hour slots are built. Each night’s darkness window can start at times like `21:30`; half-hour steps align scores with those boundaries instead of rounding to the next full hour.

| Resolution | Weather source | `:00` slots | `:30` slots |
|------------|----------------|-------------|-------------|
| Preferred | Open-Meteo `minutely_15` at `:00` / `:30` | Direct sample | Direct sample; precipitation sums two 15-min buckets |
| Fallback | Open-Meteo `hourly` | Hourly value | Linear interpolation of continuous fields; precipitation uses half the enclosing hour’s total |

The nightly card score is the average of interval scores during darkness. **Best hours** are contiguous windows where interval scores reach 70 or higher (may start or end at `:30`).

Moon impact uses two related concepts:

| Term | Meaning |
|------|---------|
| **Disk lit** | Lunar phase illumination — how much of the moon's disk is illuminated that night |
| **Avg moon sky glow** | Average effective sky brightness from moonlight during darkness; drives the nightly score |
| **Effective moon sky glow** (per interval) | Phase illumination scaled by moon altitude via `sin(altitude)`; low or below-horizon moons contribute less |

Moonrise and moonset on night cards are informational. Interval scores compute moon altitude with Skyfield at each slot’s midpoint (+15 minutes for 30-min steps). On first forecast run, Skyfield downloads a JPL ephemeris file (~16 MB) into `backend/data/ephemeris/`.

### Moon enrichment (FreeAstroAPI)

Night cards optionally show richer lunar display data and SVG phase graphics from [FreeAstroAPI](https://www.freeastroapi.com/moon). This is **UI-only enrichment** — forecast scores still use IPGeolocation disk illumination and Skyfield altitude.

| Step | Behavior |
|------|----------|
| Forecast search | Returns immediately with IPGeolocation moon text (0 FreeAstro calls) |
| Moon enrichment | Frontend calls `GET /api/moon/enrichment` after forecast loads |
| Cache hit | Phase name, age, special labels, and SVG served from server cache (0 live calls) |
| Cache miss | Backend queues fetches at **1 req/sec**; UI polls until graphics appear |
| Quota exhausted | Falls back to placeholder moon + IPGeolocation labels |

Free tier limits: **80 calls/day**, **1 request/second**. The server caches phase data globally by calendar date (shared across all users). A daily prewarm script fetches the next 7 dates (~7 calls/day) so most searches never hit the live API.

```bash
./scripts/prewarm-moon-cache.sh   # optional; requires FREEASTRO_API_KEY in backend/.env
```

### Astronomy summary (astronomy-engine)

After a forecast loads, the frontend calls `POST /api/astronomy` in parallel with moon enrichment. The backend uses [astronomy-engine](https://pypi.org/project/astronomy-engine/) locally — no API key required.

| Section | Window | Content |
|---------|--------|---------|
| **Events timeline** | Next 30 days | Lunar eclipses, local solar eclipses, Mercury/Venus transits, planetary oppositions/conjunctions (vs Sun), and bright planet–planet conjunctions (≤ ~3° separation) |
| **Planet visibility** | 7 forecast nights | For each calendar night date, whether Mercury–Neptune is above the horizon at any time that day |

Planet visibility cells include explicit **above-horizon time windows** (`windows[]` with local `start`/`end` in `HH:MM`), **peak altitude**, **peak time**, and **magnitude** at peak. Uranus and Neptune appear as muted telescope rows.

Events show a local visibility badge when they are global phenomena not guaranteed to be visible at the forecast location (e.g. transits, inferior/superior conjunctions with the Sun).

### External services

| Service | Role | API key |
|---------|------|---------|
| [IPGeolocation.io](https://ipgeolocation.io) | Geocoding, twilight windows, moon phase/times | Required |
| [Open-Meteo](https://open-meteo.com) | Hourly, 15-minutely, and daily weather | None |
| [FreeAstroAPI](https://www.freeastroapi.com/moon) | Moon phase graphics and enriched lunar labels (optional) | Optional |
| [astronomy-engine](https://pypi.org/project/astronomy-engine/) | Local eclipse, conjunction, and planet visibility calculations | None (MIT library) |

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
│   │   │   ├── moon_enrichment.py  # Pydantic schemas for moon enrichment API
│   │   │   └── astronomy.py    # Pydantic schemas for astronomy summary API
│   │   ├── routers/
│   │   │   ├── forecast.py     # POST /api/forecast orchestration
│   │   │   ├── moon_enrichment.py  # GET /api/moon/enrichment + SVG route
│   │   │   └── astronomy.py    # POST /api/astronomy
│   │   └── services/
│   │       ├── ipgeolocation.py    # Astronomy API client (geocode + time series)
│   │       ├── openmeteo.py        # Weather forecast client
│   │       ├── scoring.py          # Merge weather + astronomy into scores
│   │       ├── moon_position.py    # Skyfield moon altitude + sky-glow curve
│   │       ├── astronomy_events.py # 30-day eclipse/conjunction event search
│   │       ├── planet_visibility.py  # Per-night planet above-horizon windows
│   │       ├── astronomy_time.py   # Timezone/time helpers for astronomy-engine
│   │       ├── freeastroapi.py     # FreeAstro moon phase client
│   │       ├── moon_cache.py       # SQLite + SVG cache for moon enrichment
│   │       ├── moon_enrichment.py  # Enrichment orchestration
│   │       ├── moon_enrichment_queue.py  # 1 RPS rate-limited fetch queue
│   ├── data/ephemeris/         # Cached JPL ephemeris (gitignored, auto-downloaded)
│   ├── data/moon_cache/        # Cached FreeAstro moon SVGs + quota state (gitignored)
│   ├── tests/
│   │   ├── test_scoring.py     # Scoring and forecast assembly tests
│   │   ├── test_moon_position.py
│   │   ├── test_astronomy_events.py
│   │   ├── test_planet_visibility.py
│   │   ├── test_astronomy_routes.py
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
│   │   │   ├── HourlyScoreChart.tsx    # Unified grid: scores, dew/temp, metrics
│   │   │   ├── hourly-chart-layout.ts  # Shared column width and temperature scale helpers
│   │   │   ├── AstronomyEventsPanel.tsx  # Events timeline + planet visibility grid
│   │   │   ├── CloudBreakdown.tsx
│   │   │   ├── PrecipitationBreakdownView.tsx
│   │   │   ├── DewPointChart.tsx
│   │   │   └── ErrorBanner.tsx
│   │   ├── hooks/
│   │   │   ├── useForecast.ts  # Forecast fetch state
│   │   │   ├── useMoonEnrichment.ts  # Async FreeAstro moon graphics
│   │   │   └── useAstronomySummary.ts  # Astronomy summary fetch state
│   │   ├── lib/
│   │   │   ├── backend-client.ts   # Typed fetch wrappers for /api
│   │   │   ├── astronomy-format.ts # Astronomy panel display formatters
│   │   │   ├── moon-sample-time.ts # Dark-window sample times for moon enrichment
│   │   │   └── weather-format.ts   # Display formatters
│   │   └── types/
│   │       ├── forecast.ts
│   │       ├── moon-enrichment.ts
│   │       └── astronomy.ts
│   └── vite.config.ts          # Dev server; proxies /api → localhost:8000
│
├── e2e/                        # Playwright browser tests
│   ├── tests/app.spec.ts
│   └── fixtures/               # Mocked API responses for offline E2E
│
├── scripts/
│   ├── check-integrity.sh      # Full test/lint/build harness
│   ├── prewarm-moon-cache.sh   # Daily FreeAstro cache prewarm (7 calls)
│   └── record-e2e-fixtures.sh  # Refresh E2E fixtures from live APIs
│
├── .github/workflows/ci.yml    # Runs check-integrity.sh on push/PR
├── .github/workflows/moon-prewarm.yml  # Scheduled moon cache prewarm
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
    AstronomyRouter["/api/astronomy"]
    AstroEngine[astronomy-engine]
  end
  subgraph external [External APIs]
    IPGeo[IPGeolocation]
    OpenMeteo[Open-Meteo]
  end
  UI --> ForecastRouter
  ForecastRouter --> IPGeo
  ForecastRouter --> OpenMeteo
  ForecastRouter --> Scoring
  Scoring --> MoonPos[moon_position Skyfield]
  UI --> AstronomyRouter
  AstronomyRouter --> AstroEngine
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Free API key from [IPGeolocation.io](https://ipgeolocation.io)
- Optional [FreeAstroAPI](https://www.freeastroapi.com/moon) key for moon phase SVG enrichment

Open-Meteo requires no API key.

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Fill in IPGEOLOCATION_API_KEY (see Prerequisites)

# Recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

On macOS, if `pip` is not found, use `python3 -m pip` instead of `pip`.

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
pip install -r requirements-dev.txt   # or: python -m pip install -r requirements-dev.txt
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

E2E tests mock `/api/forecast`, `/api/astronomy`, and `/api/moon/enrichment` in the browser — no backend or external APIs required.

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

Live backend integration (~2 paid external API calls; requires valid `backend/.env`):

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
| `--live` | ~2 paid (2 IPGeolocation; Open-Meteo and astronomy-engine are free/local) |

Refresh E2E fixtures from live responses when API shapes change (forecast via IPGeolocation; astronomy summary computed locally):

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
| `POST /api/forecast` | 7-day stargazing forecast for an address | 2 IPGeolocation + 1 Open-Meteo (hourly + minutely_15) |
| `GET /api/moon/enrichment` | Cached FreeAstro moon phase labels and SVG URLs | 0 when cached; 1/date on miss (queued at 1 RPS) |
| `GET /api/moon/visual/{date}.svg` | Cached moon phase SVG | 0 |
| `POST /api/astronomy` | 30-day event timeline + 7-night planet visibility | 0 (local astronomy-engine) |

### Astronomy response fields

| Field | Description |
|-------|-------------|
| `events[]` | Upcoming events sorted by `start_at`; categories include `lunar_eclipse`, `solar_eclipse`, `transit`, `conjunction`, `opposition` |
| `events[].visible_locally` | Whether the event is expected to be observable at the request coordinates |
| `planet_visibility[]` | One entry per requested forecast night date |
| `planet_visibility[].planets[].windows[]` | Local above-horizon intervals (`start`/`end` as `HH:MM`) on that calendar day |
| `planet_visibility[].planets[].visible` | `true` when at least one window exists |

### Forecast response fields

| Field | Description |
|-------|-------------|
| `score_step_minutes` | `30` when scores use half-hour slots; `60` when only hourly weather is available |
| `nights[].hourly` | Time-series score intervals during darkness (includes `:30` times when step is 30) |
| `nights[].moon_sky_glow_avg` | Average effective moon sky glow during darkness |
| `nights[].best_hours` | Contiguous high-score windows; may start or end at `:30` |

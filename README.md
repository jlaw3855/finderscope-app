# Finderscope

A full-stack web app for stargazers. Enter an address to get a 7-day stargazing weather forecast and generate a custom star chart for any date and time.

## Architecture

- **`backend/`** — FastAPI server (API keys, external API calls, scoring logic)
- **`frontend/`** — React + Vite client (UI only, no secrets)

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

1. Backend unit and route tests (`pytest`, excludes `live`)
2. Frontend unit tests (`vitest`)
3. E2E browser tests (`playwright`, mocked APIs)
4. Frontend lint (`oxlint`)
5. TypeScript compile (`tsc -b`)
6. Production build (`vite build`) — skipped with `--fast`
7. Live backend integration — only with `--live`

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
python tests/fixtures/generate_e2e_responses.py
```

A project Cursor skill at `.cursor/skills/integrity-check/` instructs the agent to run these checks before completing coding tasks.

## Continuous integration

GitHub Actions runs `./scripts/check-integrity.sh` on every push and pull request to `main`.
Live API tests are not run in CI.

## API Usage

| Endpoint | Description | External calls |
|----------|-------------|----------------|
| `POST /api/forecast` | 7-day stargazing forecast for an address | 2 IPGeolocation + 1 Open-Meteo |
| `POST /api/star-chart` | Generate a star chart image URL | 1 AstronomyAPI |

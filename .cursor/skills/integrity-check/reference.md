# Integrity Check Reference

Run these from the repository root when isolating a failing stage.

## Backend (pytest)

```bash
cd backend
python -m pytest
python -m pytest tests/test_scoring.py -k darkness
python -m pytest tests/test_routes.py -v
python -m pytest --cov=app --cov-report=term-missing
```

Live integration (requires `backend/.env` keys):

```bash
cd backend
FINDERSCOPE_LIVE_TESTS=1 python -m pytest -m live -o addopts=
```

Install dev dependencies once:

```bash
cd backend
pip install -r requirements-dev.txt
```

## Frontend (Vitest)

```bash
cd frontend
npm run test:run
npm run test:run -- src/lib/weather-format.test.ts
npm run test -- --coverage
```

## E2E (Playwright)

```bash
cd e2e
npm install
npm run test:install   # first time only — installs Chromium
npm run test
```

Regenerate Playwright visual baselines after intentional UI/CSS changes:

```bash
cd e2e
npm run test:visual:update
```

Regenerate mocked E2E fixtures from scoring fixtures (no API calls):

```bash
cd backend
python tests/fixtures/generate_e2e_responses.py
```

Record live API responses into E2E fixtures (~4 paid calls):

```bash
chmod +x scripts/record-e2e-fixtures.sh
./scripts/record-e2e-fixtures.sh
```

## Lint and compile

```bash
cd frontend
npm run lint
npx tsc -b
npx vite build
```

Install frontend dependencies once:

```bash
cd frontend
npm install
```

## Full harness

```bash
chmod +x scripts/check-integrity.sh   # first time only
./scripts/check-integrity.sh
./scripts/check-integrity.sh --fast
./scripts/check-integrity.sh --live   # adds live backend integration
```

For local dev servers (uvicorn + Vite), see `.cursor/skills/run-dev/`.

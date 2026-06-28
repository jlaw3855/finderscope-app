---
name: dev-setup
description: >-
  Installs Finderscope dev dependencies and configures backend/.env (venv,
  pip, npm). Use on first clone, after dependency changes, or when the user
  asks to set up, install, or configure the local development environment.
---

# Finderscope Dev Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- Free API key from [IPGeolocation.io](https://ipgeolocation.io) (required for live forecast search)
- Optional [FreeAstroAPI](https://www.freeastroapi.com/moon) key for moon SVG enrichment

Open-Meteo requires no API key.

## Backend

From the repository root:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set `IPGEOLOCATION_API_KEY`. Optionally set `FREEASTRO_API_KEY`.

Recommended virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For running tests or integrity checks, also install dev dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

On macOS, if `pip` is not found, use `python3 -m pip` instead of `pip`.

## Frontend

```bash
cd frontend
npm install
```

## E2E (optional)

Only needed for Playwright browser tests or visual baseline work:

```bash
cd e2e
npm install
npm run test:install   # first time only — installs Chromium
```

## Security

- Never commit `backend/.env` or other secrets
- Remind the user to paste API keys locally; do not embed keys in code or skills

## Next step

After setup completes, use the **run-dev** skill to start backend and frontend dev servers.

For environment variable details, see [reference.md](reference.md).

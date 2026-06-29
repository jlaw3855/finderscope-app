# Run Dev Reference

## URLs and ports

| Service | URL | Default port |
|---------|-----|--------------|
| Frontend (Vite) | `http://localhost:5173` | `5173` |
| Backend (FastAPI) | `http://127.0.0.1:8000` | `8000` |
| Health check | `http://127.0.0.1:8000/health` | — |
| API docs | `http://127.0.0.1:8000/docs` | — |

Override ports when stopping: `BACKEND_PORT=8001 FRONTEND_PORT=5174 ./scripts/stop-dev-servers.sh`

Proxy config: `frontend/vite.config.ts` forwards `/api` → `localhost:8000`.

## Stop script

[`scripts/stop-dev-servers.sh`](../../../scripts/stop-dev-servers.sh) kills listeners on the backend and frontend dev ports using `lsof`. Safe to run when nothing is listening (no-op).

## Python resolution

Prefer the project venv when present (same as `scripts/check-integrity.sh`):

1. `backend/.venv/bin/python`
2. `python3` on PATH

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Address already in use` | Stale uvicorn or Vite | Run `./scripts/stop-dev-servers.sh`, then restart |
| UI loads but forecast search fails | Backend not running or wrong port | Start uvicorn on `:8000`; check `curl /health` |
| CORS errors in browser | Origin not in `CORS_ORIGINS` | Default `http://localhost:5173` in `.env.example`; add your origin if needed |
| 401/403 from IPGeolocation | Missing or invalid API key; OS env override; `.env` BOM/CRLF/UTF-16; plan lacks Astronomy v3 | Set `IPGEOLOCATION_API_KEY` in `backend/.env` (no quotes); save as UTF-8; restart backend; see **IPGeolocation diagnostics** below |
| Moon SVGs never appear | No FreeAstro key or quota | Optional; set `FREEASTRO_API_KEY` or use forecast without enrichment |
| Seeing/transparency always show visibility fallback | Outside 7timer ~3-day window or API miss | Expected for forecast nights 4–7; check `SEVENTIMER_ENABLED=true` and network to `7timer.info` |
| `ZoneInfoNotFoundError` on Windows | Missing `tzdata` | Re-run `pip install -r requirements.txt` in `backend/` (installs `tzdata` on win32) |
| Stop script finds no PIDs but port busy | Process owned by another user or different bind | `lsof -i :8000` / `:5173` manually; adjust `BACKEND_PORT` / `FRONTEND_PORT` |

### IPGeolocation diagnostics

On startup the backend logs warnings for empty keys, BOM/CRLF/quotes, UTF-16 `.env`, or when an OS environment variable overrides `backend/.env`.

**Key health check (does not print the secret):**

```bash
cd backend
python -c "from app.config import get_settings, describe_api_key_health, get_ipgeolocation_key_source; s=get_settings(); print(describe_api_key_health(s.ipgeolocation_api_key, source=get_ipgeolocation_key_source()))"
```

Set `FINDERSCOPE_DEBUG_CONFIG=1` before starting uvicorn to log the same health dict at INFO level.

**Windows — stale env var overriding `.env`:**

```powershell
echo $env:IPGEOLOCATION_API_KEY
Remove-Item Env:IPGEOLOCATION_API_KEY
```

**Direct API test:**  
`https://api.ipgeolocation.io/v3/astronomy?apiKey=YOUR_KEY&location=Denver,CO`

If health flags are clean but the API returns 401, verify your IPGeolocation plan includes Astronomy v3 — that is not an OS issue.

See also **dev-setup** reference for the full Windows / macOS / Linux matrix.

## Related skills

- **dev-setup** — first-time install and `.env` configuration
- **integrity-check** — pytest, vitest, Playwright, lint, and build (not dev servers)

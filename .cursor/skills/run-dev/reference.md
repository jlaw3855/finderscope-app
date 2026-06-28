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
| 401/403 from IPGeolocation | Missing or invalid API key | Set `IPGEOLOCATION_API_KEY` in `backend/.env` |
| Moon SVGs never appear | No FreeAstro key or quota | Optional; set `FREEASTRO_API_KEY` or use forecast without enrichment |
| Stop script finds no PIDs but port busy | Process owned by another user or different bind | `lsof -i :8000` / `:5173` manually; adjust `BACKEND_PORT` / `FRONTEND_PORT` |

## Related skills

- **dev-setup** — first-time install and `.env` configuration
- **integrity-check** — pytest, vitest, Playwright, lint, and build (not dev servers)

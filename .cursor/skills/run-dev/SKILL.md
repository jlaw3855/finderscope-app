---
name: run-dev
description: >-
  Stops stale Finderscope dev processes, then starts backend (uvicorn) and
  frontend (Vite) dev servers. Use when the user asks to run or restart the app,
  start dev servers, open localhost, or develop against the live API proxy.
---

# Finderscope Run Dev

## Prerequisite

- `backend/.env` exists with `IPGEOLOCATION_API_KEY` set
- Dependencies installed (see **dev-setup** skill if not)

## Restart workflow

Always stop stale dev servers **before** starting new ones (avoids `Address already in use` and orphaned uvicorn/Vite processes).

From the repository root:

```bash
chmod +x scripts/stop-dev-servers.sh   # first time only
./scripts/stop-dev-servers.sh
```

Or inline (macOS/Linux, when the script is unavailable):

```bash
for port in 8000 5173; do
  pids=$(lsof -ti tcp:${port} 2>/dev/null || true)
  if [ -n "$pids" ]; then kill $pids 2>/dev/null || kill -9 $pids 2>/dev/null || true; fi
done
```

Optional: verify ports are free — `curl` to `/health` or `:5173` should fail until servers are restarted.

## Start order

Start the **backend before the frontend**. Vite proxies `/api` to `http://localhost:8000`.

## Backend (background terminal)

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If no venv exists, fall back to:

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API base: `http://127.0.0.1:8000`

## Frontend (background terminal)

```bash
cd frontend
npm run dev
```

UI: `http://localhost:5173` (proxies `/api` to the backend)

## Verify

```bash
curl -s http://127.0.0.1:8000/health
```

Open `http://localhost:5173` and search e.g. `Denver, CO`.

## Agent behavior

1. Run `./scripts/stop-dev-servers.sh` from the repo root (or inline port kill)
2. Start backend, then frontend in **background** terminals (`block_until_ms: 0`)
3. Poll until `/health` returns `{"status":"ok"}` and `http://localhost:5173` responds
4. Do **not** use `./scripts/check-integrity.sh --live` for routine dev
5. For tests, lint, or production build, use the **integrity-check** skill instead

If servers are already healthy and the user did not ask to restart, skip the stop step.

## Not daily dev

| Command | Purpose |
|---------|---------|
| `cd frontend && npm run preview` | Serves a **production** build (run `vite build` first) |
| `./scripts/check-integrity.sh` | Full test/lint/build harness |

## Troubleshooting

See [reference.md](reference.md) for ports, CORS, and common failures.

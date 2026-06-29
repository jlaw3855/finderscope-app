#!/usr/bin/env bash
# * Smoke-test the production Docker image locally.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f backend/.env ]]; then
  echo "ERROR: backend/.env not found. Copy backend/.env.example and set IPGEOLOCATION_API_KEY." >&2
  exit 1
fi

echo "Building and starting production container..."
docker compose up -d --build

echo "Waiting for /health..."
for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 2
done

health="$(curl -sf http://127.0.0.1:8000/health)"
echo "Health: $health"

if ! curl -sf http://127.0.0.1:8000/ | grep -qi '<html'; then
  echo "ERROR: GET / did not return HTML" >&2
  exit 1
fi

echo "Production smoke test passed. Open http://localhost:8000"

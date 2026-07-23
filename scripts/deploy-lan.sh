#!/usr/bin/env bash
# * Deploy Finderscope LAN stack from prebuilt GHCR image (deploy/lan).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAN_DIR="$ROOT_DIR/deploy/lan"
BACKEND_ENV="$ROOT_DIR/backend/.env"
LAN_ENV="$LAN_DIR/.env"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--skip-stop-dev]

Pulls ghcr.io/jlaw3855/finderscope-app and starts the LAN compose stack.
See docs/DEPLOYMENT-LAN.md for CORS and multi-device access.

Options:
  --skip-stop-dev   Do not stop uvicorn/Vite on ports 8000/5173 first
EOF
}

SKIP_STOP=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-stop-dev)
      SKIP_STOP=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  if [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    export DOCKER_CLI_PLUGIN_PATH="/Applications/Docker.app/Contents/Resources/cli-plugins"
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found. Install Docker Desktop and retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  if [[ -d /Applications/Docker.app ]]; then
    echo "Starting Docker Desktop..."
    open -a Docker
    for _ in $(seq 1 60); do
      if docker info >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done
  fi
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running. Start Docker Desktop and retry." >&2
  exit 1
fi

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "ERROR: docker compose is not available." >&2
    exit 1
  fi
}

if [[ ! -f "$LAN_ENV" ]]; then
  if [[ ! -f "$LAN_DIR/.env.example" ]]; then
    echo "ERROR: $LAN_DIR/.env.example not found." >&2
    exit 1
  fi
  cp "$LAN_DIR/.env.example" "$LAN_ENV"
  if [[ -f "$BACKEND_ENV" ]]; then
    # * Seed API keys from dev .env when present (never printed).
    while IFS= read -r key; do
      value="$(grep -E "^${key}=" "$BACKEND_ENV" 2>/dev/null | head -1 | cut -d= -f2- || true)"
      if [[ -n "$value" ]]; then
        if grep -q "^${key}=" "$LAN_ENV"; then
          sed -i.bak "s|^${key}=.*|${key}=${value}|" "$LAN_ENV" && rm -f "$LAN_ENV.bak"
        else
          echo "${key}=${value}" >> "$LAN_ENV"
        fi
      fi
    done <<'KEYS'
IPGEOLOCATION_API_KEY
NASA_API_KEY
FREEASTRO_API_KEY
KEYS
    echo "Created $LAN_ENV from .env.example (seeded keys from backend/.env)."
  else
    echo "Created $LAN_ENV from .env.example — set IPGEOLOCATION_API_KEY before continuing."
  fi
fi

if ! grep -qE '^IPGEOLOCATION_API_KEY=.+' "$LAN_ENV"; then
  echo "ERROR: IPGEOLOCATION_API_KEY is empty in $LAN_ENV" >&2
  exit 1
fi

if [[ "$SKIP_STOP" == false ]] && [[ -x "$ROOT_DIR/scripts/stop-dev-servers.sh" ]]; then
  echo "Stopping dev servers on ports 8000/5173..."
  "$ROOT_DIR/scripts/stop-dev-servers.sh" || true
fi

cd "$LAN_DIR"
echo "Pulling LAN image..."
compose_cmd pull
echo "Starting LAN stack..."
compose_cmd up -d

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

echo "LAN deployment ready. Open http://localhost:8000"
echo "For other devices, set CORS_ORIGINS in deploy/lan/.env to your LAN IP (see docs/DEPLOYMENT-LAN.md)."

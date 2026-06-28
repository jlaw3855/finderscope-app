#!/usr/bin/env bash
# * Stops Finderscope dev servers bound to the default backend/frontend ports.
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

stop_port() {
  local port="$1"
  local label="$2"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -z "${pids}" ]]; then
      pids="$(lsof -ti ":${port}" 2>/dev/null || true)"
    fi
  fi

  if [[ -z "${pids}" ]]; then
    echo "No listener on port ${port} (${label})"
    return 0
  fi

  echo "Stopping port ${port} (${label}): ${pids//$'\n'/ }"
  # shellcheck disable=SC2086
  kill ${pids} 2>/dev/null || true
  sleep 0.3
  # shellcheck disable=SC2086
  if kill -0 ${pids} 2>/dev/null; then
    # shellcheck disable=SC2086
    kill -9 ${pids} 2>/dev/null || true
  fi
}

stop_port "${BACKEND_PORT}" "backend"
stop_port "${FRONTEND_PORT}" "frontend"

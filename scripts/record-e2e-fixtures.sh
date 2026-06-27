#!/usr/bin/env bash
# * Records live API responses for E2E fixture refresh (~2 paid external calls).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/e2e/fixtures"
FORECAST_OUT="$OUTPUT_DIR/forecast-response.json"
ASTRONOMY_OUT="$OUTPUT_DIR/astronomy-response.json"

resolve_python() {
  if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
    echo "$ROOT_DIR/backend/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  else
    echo "python"
  fi
}

PYTHON_BIN="$(resolve_python)"

if [[ ! -f "$ROOT_DIR/backend/.env" ]]; then
  echo "backend/.env is required to record live fixtures." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Recording live forecast for Denver, CO..."
FORECAST_JSON="$(cd "$ROOT_DIR/backend" && FINDERSCOPE_LIVE_TESTS=1 "$PYTHON_BIN" - <<'PY'
import json
import os

os.environ["FINDERSCOPE_LIVE_TESTS"] = "1"

from fastapi.testclient import TestClient

from app.main import app

with TestClient(app) as client:
    response = client.post("/api/forecast", json={"address": "Denver, CO"})

if response.status_code != 200:
    raise SystemExit(f"Forecast request failed: {response.status_code} {response.text}")

print(json.dumps(response.json()))
PY
)"

printf '%s\n' "$FORECAST_JSON" > "$FORECAST_OUT"
echo "Wrote $FORECAST_OUT"

echo "Recording local astronomy summary..."
ASTRONOMY_JSON="$(cd "$ROOT_DIR/backend" && "$PYTHON_BIN" - <<'PY'
import json

from fastapi.testclient import TestClient

from app.main import app

forecast = json.loads(open("../e2e/fixtures/forecast-response.json", encoding="utf-8").read())
location = forecast["location"]
dates = [night["date"] for night in forecast["nights"]]

with TestClient(app) as client:
    response = client.post(
        "/api/astronomy",
        json={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timezone": location["timezone"],
            "dates": dates,
        },
    )

if response.status_code != 200:
    raise SystemExit(f"Astronomy request failed: {response.status_code} {response.text}")

print(json.dumps(response.json()))
PY
)"

printf '%s\n' "$ASTRONOMY_JSON" > "$ASTRONOMY_OUT"
echo "Wrote $ASTRONOMY_OUT"

echo "Done. Review git diff before committing fixture updates."

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" "$ROOT/scripts/prewarm_moon_cache.py"

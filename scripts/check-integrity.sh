#!/usr/bin/env bash
# * Runs Finderscope integrity checks from the repository root.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAST_MODE=false
LIVE_MODE=false
DEMO_MODE=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [--fast] [--live] [--demo]

  (default)  Backend lint, backend tests, frontend tests, E2E tests, lint, TypeScript compile, production build
  --fast     Skip the Vite production build
  --live     Also run backend live integration tests (~4 paid external API calls)
  --demo     Also run DSO demo E2E tests (e2e/tests/dso-demo.spec.ts)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fast)
      FAST_MODE=true
      shift
      ;;
    --live)
      LIVE_MODE=true
      shift
      ;;
    --demo)
      DEMO_MODE=true
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

run_stage() {
  local name="$1"
  shift
  echo ""
  echo "==> $name"
  "$@"
  echo "PASS  $name"
}

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

cd "$ROOT_DIR"

run_stage "Backend lint (ruff)" bash -c "cd backend && ruff check app tests"
run_stage "Backend tests (pytest)" bash -c "cd backend && \"$PYTHON_BIN\" -m pytest"
run_stage "Frontend unit tests (vitest)" bash -c "cd frontend && npm run test:run"
run_stage "E2E browser tests (Playwright)" bash -c "cd e2e && npm run test"

if [[ "$DEMO_MODE" == true ]]; then
  run_stage "DSO demo E2E (Playwright)" bash -c "cd e2e && PLAYWRIGHT_DEMO=1 npx playwright test tests/dso-demo.spec.ts tests/dso-demo-v2.spec.ts"
else
  echo ""
  echo "SKIP  DSO demo E2E (Playwright) [use --demo to enable]"
fi
run_stage "Frontend lint (oxlint)" bash -c "cd frontend && npm run lint"
run_stage "Frontend TypeScript compile (tsc)" bash -c "cd frontend && npx tsc -b"

if [[ "$FAST_MODE" == false ]]; then
  run_stage "Frontend production build (vite)" bash -c "cd frontend && npx vite build"
else
  echo ""
  echo "SKIP  Frontend production build (vite) [--fast]"
fi

if [[ "$LIVE_MODE" == true ]]; then
  run_stage "Backend live integration (pytest -m live)" bash -c "cd backend && FINDERSCOPE_LIVE_TESTS=1 \"$PYTHON_BIN\" -m pytest -m live -o addopts="
else
  echo ""
  echo "SKIP  Backend live integration (pytest -m live) [use --live to enable]"
fi

echo ""
echo "All integrity checks passed."

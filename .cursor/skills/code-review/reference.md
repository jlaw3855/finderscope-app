# Code Review Reference

Shared checklists for the local code-review skill and the PR agent review script (`scripts/agent_pr_review.py`). PR reviews use the same severity rules; CI runs `check-integrity.sh` separately.

## Backend

### External APIs — fail open

When an optional upstream fails, return a successful HTTP response with degraded data — not a 500.

- Pattern: [`backend/app/routers/forecast.py`](../../backend/app/routers/forecast.py) `_fetch_astro_if_enabled` catches `SevenTimerError` and unexpected errors, sets `astro_data_unavailable`, logs a warning
- Invalid JSON from upstream should be wrapped as a domain error before the router (see [`backend/app/services/seventimer.py`](../../backend/app/services/seventimer.py))
- New optional integrations should follow the same pattern and add response flags in [`backend/app/models/`](../../backend/app/models/)

### Secrets and configuration

- API keys only via [`backend/app/config.py`](../../backend/app/config.py) `Settings` and `backend/.env`
- Never commit `.env`, keys, or tokens
- Log key health with `describe_api_key_health` — never log raw key values
- Document new env vars in README and `.env.example` when they affect setup

### Models and API contract

- Pydantic models in [`backend/app/models/`](../../backend/app/models/) match frontend types in [`frontend/src/types/`](../../frontend/src/types/)
- New public response fields need README API table updates when user-visible
- Use Google-style docstrings on public router and service functions

### Tests

- New routes: tests in [`backend/tests/test_routes.py`](../../backend/tests/test_routes.py) or focused modules
- New services: unit tests with mocks (`respx` for HTTP)
- Scoring logic: [`backend/tests/test_scoring.py`](../../backend/tests/test_scoring.py)

### Lint

- Backend lint: `cd backend && ruff check app tests` (also in integrity harness)
- See [../integrity-check/reference.md](../integrity-check/reference.md) for isolated pytest commands

## Frontend

### Types and API alignment

- Forecast and astronomy types in [`frontend/src/types/`](../../frontend/src/types/) must match backend Pydantic models
- Handle degraded responses (e.g. `astro_data_unavailable`) with user-visible notices, not silent failure

### Preferences and storage

- `localStorage` keys centralized in dedicated libs (e.g. [`frontend/src/lib/panel-blur-preference.ts`](../../frontend/src/lib/panel-blur-preference.ts))
- No scattered magic strings for storage keys

### Accessibility

- Interactive controls: visible labels, `aria-pressed` / `aria-label` on toggles
- Chart and panel content readable when panel blur is disabled (opaque panel classes under `.app--no-panel-blur`)

### CSS scope

- Prefer scoped classes (`.panel`, `.app--no-panel-blur`, component-specific panels)
- Avoid unscoped global overrides that leak outside the app shell

### Tests

- Formatters and toggles: Vitest in [`frontend/src/lib/`](../../frontend/src/lib/) and [`frontend/src/components/`](../../frontend/src/components/)
- CSS or layout changes: note if Playwright visual baselines in `e2e/` need updating

## Cross-cutting

- Minimal diff scope — no unrelated refactors in the same PR
- README updates when behavior, setup, or API contracts change
- No secrets in git history or committed files
- [`scripts/check-integrity.sh`](../../scripts/check-integrity.sh) is the single source of truth for automated gates (same as CI)

## PR agent review (GitHub)

Every pull request to `main` triggers [`.github/workflows/agent-review.yml`](../../.github/workflows/agent-review.yml) when `CURSOR_API_KEY` is configured:

| Mode | Trigger | Effect |
|------|---------|--------|
| **Advisory** | Default | Posts/updates a PR comment; job succeeds unless SDK startup fails |
| **Strict** | PR label `agent-review:strict` or manual workflow dispatch with `strict: true` | Job fails on Critical/High findings in the agent report |

The PR agent does **not** run the integrity harness — [`ci.yml`](../../.github/workflows/ci.yml) owns that.

Setup: add repository secret `CURSOR_API_KEY` (Cursor Dashboard → API Keys). See [../../docs/CODE_REVIEW.md](../../docs/CODE_REVIEW.md).

## Required agent report sections (PR script)

The PR review script expects this structure in the agent output:

```markdown
## Agent review summary
- Mode: advisory | strict
- Integrity note: CI runs check-integrity.sh separately

### Findings
| Severity | Location | Source | Finding | Action |
|----------|----------|--------|---------|--------|
```

Severity values: `Critical`, `High`, `Medium`, `Low`, or `None` for an empty table row stating no issues.

## Isolated commands

Full harness:

```bash
./scripts/check-integrity.sh
```

Backend lint only:

```bash
cd backend && ruff check app tests
```

More stage commands: [../integrity-check/reference.md](../integrity-check/reference.md).

## Windows

Run `./scripts/check-integrity.sh` from **Git Bash** or **WSL**. PowerShell alone does not execute bash harness scripts reliably.

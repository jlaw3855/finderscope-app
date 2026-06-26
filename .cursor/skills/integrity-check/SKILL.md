---
name: integrity-check
description: >-
  Runs Finderscope integrity checks (pytest, vitest, Playwright E2E, lint,
  build) via scripts/check-integrity.sh. Use after modifying backend,
  frontend, e2e, or scripts code, before marking a task complete, or when
  the user asks for integrity verification or tests.
---

# Finderscope Integrity Check

## When to run

Run integrity checks when any of these apply:

- You edited files under `backend/`, `frontend/`, `e2e/`, or `scripts/`
- You are about to mark a coding task complete
- The user asks to verify integrity, run tests, or confirm the build

## Command

From the repository root:

```bash
./scripts/check-integrity.sh
```

Use `--fast` only for mid-task sanity checks (skips the Vite production build):

```bash
./scripts/check-integrity.sh --fast
```

Use `--live` only when the user explicitly requests live API verification or fixture recording (~4 paid external API calls):

```bash
./scripts/check-integrity.sh --live
```

Always run the **full** harness (no `--fast`) before declaring work done. Do **not** use `--live` during routine development.

## Failure loop

1. Read the failing stage output
2. Fix the root cause in source (not by skipping checks)
3. Re-run `./scripts/check-integrity.sh`
4. Repeat until exit code is `0`

Do not skip stages or mark tasks complete while any stage fails.

## Scope rules

- Default harness uses mocks and fixtures — no live API keys required
- E2E Playwright tests mock `/api/*` in the browser (zero external calls)
- Never commit `backend/.env` or other secrets
- `frontend/dist/` is build output, not a source-of-truth check target
- GitHub Actions runs the same default harness on push and PR to `main` (no `--live`)

## Report format

After running checks, summarize briefly:

```markdown
## Integrity check
- Backend tests: pass/fail
- Frontend tests: pass/fail
- E2E browser tests: pass/fail
- Lint: pass/fail
- TypeScript compile: pass/fail
- Production build: pass/fail (or skipped with --fast)
- Live integration: pass/fail/skipped
- Fixes applied: [files, if any]
```

## Debugging

If a stage fails and you need isolated commands, see [reference.md](reference.md).

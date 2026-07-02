---
name: code-review
description: >-
  Orchestrates Finderscope pre-merge code review: integrity harness, parallel
  Bugbot and Security subagent reviews, and repo-specific checklists. Use when
  the user asks for code review, before opening a PR, after substantial feature
  work, or before marking a multi-file task complete.
---

# Finderscope Code Review

## When to run

Run this workflow when any of these apply:

- The user asks for a code review or merge-readiness check
- You are about to open a pull request
- You finished substantial work across backend, frontend, or both
- You are about to mark a multi-file task complete

For tests only (no review orchestration), use the **integrity-check** skill instead.

## Workflow (ordered)

### 1. Scope the diff

- **Default:** `branch changes` vs `main` merge-base (committed + uncommitted)
- **Override:** `uncommitted changes` only when the user requests it

### 2. Automated gates (blocking)

From the repository root:

```bash
./scripts/check-integrity.sh
```

- Do **not** use `--fast` for final review
- Fix failures before proceeding; re-run until exit code `0`
- Same harness as [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)

### 3. Subagent reviews (parallel, readonly)

Launch **both** in parallel:

1. **Bugbot** — follow the global `review-bugbot` skill with `Diff: branch changes` (or `uncommitted changes`)
2. **Security Review** — follow the global `review-security` skill with the same diff scope

Do **not** auto-fix findings; triage them in the report.

### 4. Domain checklist

Walk through [reference.md](reference.md) for backend, frontend, and cross-cutting items relevant to the diff.

### 5. Report (required output)

```markdown
## Code review summary
- Scope: branch changes | uncommitted
- Integrity harness: pass/fail (+ stages)
- Bugbot: N findings / none
- Security: N findings / none
- Checklist: pass / issues noted
- PR agent review: advisory on every PR to main; add label `agent-review:strict` for blocking mode

### Findings (severity order)
| Severity | Location | Source | Finding | Action |
|----------|----------|--------|---------|--------|

### Recommended next steps
- [ ] Fix blocking items
- [ ] Optional follow-ups
```

### 6. Exit criteria

- Integrity pass required for **merge-ready**
- Bugbot/Security **Critical/High** must be fixed or explicitly accepted by the user
- Medium/Low documented in the report

## Windows note

`check-integrity.sh` requires Git Bash or WSL on Windows. See [reference.md](reference.md) for isolated stage commands.

## Related

- Checklists and expanded guidance: [reference.md](reference.md)
- Integrity harness only: [../integrity-check/SKILL.md](../integrity-check/SKILL.md)
- Human-readable overview: [../../docs/CODE_REVIEW.md](../../docs/CODE_REVIEW.md)

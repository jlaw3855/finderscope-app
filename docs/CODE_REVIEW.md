# Code review

Finderscope uses two aligned review layers plus deterministic CI.

## Layers

| Layer | When | What runs | Blocks merge? |
|-------|------|-----------|---------------|
| **Local (Cursor skill)** | Before PR / on request | `check-integrity.sh` → Bugbot + Security subagents → checklist | Developer gate only |
| **CI** | Every push/PR to `main` | [`scripts/check-integrity.sh`](../scripts/check-integrity.sh) | Yes |
| **PR agent review** | Every PR to `main` | [`scripts/agent_pr_review.py`](../scripts/agent_pr_review.py) via Cursor SDK | Advisory by default |

Shared checklists live in [`.cursor/skills/code-review/reference.md`](../.cursor/skills/code-review/reference.md).

## Local pre-merge review

Use the **code-review** skill (`.cursor/skills/code-review/SKILL.md`):

```bash
./scripts/check-integrity.sh
```

Then run Bugbot and Security subagents in parallel (readonly), walk the checklist, and produce the report template from the skill.

On Windows, run the harness from **Git Bash** or **WSL**.

## Automated PR review

Workflow: [`.github/workflows/agent-review.yml`](../.github/workflows/agent-review.yml)

### Setup (one time)

1. Create a Cursor API key:
   - Personal: [Cursor Dashboard → API Keys](https://cursor.com/dashboard/api)
   - Team CI: [Service accounts](https://cursor.com/docs/account/enterprise/service-accounts)
2. Add GitHub repository secret **`CURSOR_API_KEY`** (Settings → Secrets and variables → Actions).
3. Ensure your Cursor team has **GitHub connected** to this repository (required for cloud agents).

If `CURSOR_API_KEY` is not set, the workflow skips with a notice job.

### Modes

| Mode | How to enable | Behavior |
|------|---------------|----------|
| **Advisory** | Default | Posts or updates a PR comment (`<!-- finderscope-agent-review -->`). Job fails only on SDK startup errors. |
| **Strict** | Add PR label `agent-review:strict` | Job also fails when the agent report contains **Critical** or **High** findings. |

The PR agent does **not** run the integrity harness — [`ci.yml`](../.github/workflows/ci.yml) owns tests, lint, and build.

### Local dry-run (optional)

```bash
pip install -r scripts/agent_pr_review_requirements.txt
export CURSOR_API_KEY=your-key
python scripts/agent_pr_review.py --base main --head your-branch --repo owner/repo --strict false
```

Parse an existing report without calling the API:

```bash
python scripts/agent_pr_review.py --parse-only report.md --strict true
```

## Rollback

All review infrastructure is config and scripts — no application runtime changes.

| Disable | Action |
|---------|--------|
| PR agent only | Remove `CURSOR_API_KEY` secret or delete `.github/workflows/agent-review.yml` |
| Strict blocking | Stop using label `agent-review:strict`; do not require the agent-review job in branch protection |
| Backend Ruff in CI | Revert the ruff stage in `check-integrity.sh` and `backend/ruff.toml` |
| Local skill | Delete `.cursor/skills/code-review/` |
| Full rollback | Revert the implementation commit(s) on `main` |

## Optional alternatives

- **Cursor Automations** (dashboard git triggers) can run similar review prompts without committing a workflow; this repo implements the GitHub Actions + SDK path instead.
- Third-party PR bots (CodeRabbit, etc.) are out of scope for this setup.

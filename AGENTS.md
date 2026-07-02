# Agent instructions

Before opening a pull request, run the **code-review** skill (`.cursor/skills/code-review/`):

1. Full `./scripts/check-integrity.sh`
2. Parallel Bugbot and Security subagent reviews
3. Domain checklist and merge-ready report

See [docs/CODE_REVIEW.md](docs/CODE_REVIEW.md) for local vs PR review layers and rollback.

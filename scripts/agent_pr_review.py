#!/usr/bin/env python3
"""Run Finderscope PR agent review via the Cursor SDK (cloud agent)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHECKLIST = ROOT_DIR / ".cursor" / "skills" / "code-review" / "reference.md"
BLOCKING_SEVERITIES = frozenset({"critical", "high"})
FINDINGS_HEADER = "### Findings"


def load_checklist(path: Path) -> str:
    """Loads the shared code-review checklist markdown."""
    if not path.is_file():
        raise FileNotFoundError(f"Checklist not found: {path}")
    return path.read_text(encoding="utf-8")


def build_prompt(
    checklist: str,
    *,
    repo: str,
    base_ref: str,
    head_ref: str,
    strict: bool,
    pr_url: str | None,
) -> str:
    """Builds the review prompt for the cloud agent."""
    mode = "strict" if strict else "advisory"
    pr_line = f"- Pull request: {pr_url}" if pr_url else "- Pull request: (local dry-run)"
    return f"""You are reviewing a GitHub pull request for the Finderscope astronomy weather app.

Repository: {repo}
Base branch: {base_ref}
Head branch: {head_ref}
{pr_line}
Review mode: {mode}

Review the diff between `{base_ref}` and `{head_ref}`. Focus on:
- Logic bugs and regressions
- Security issues (secrets, injection, unsafe defaults)
- Finderscope conventions in the checklist below

Do NOT run tests or linters — CI runs check-integrity.sh separately.

## Checklist (from project reference)

{checklist}

## Required output format

Respond with ONLY the following markdown (no extra preamble):

## Agent review summary
- Mode: {mode}
- Integrity note: CI runs check-integrity.sh separately

### Findings
| Severity | Location | Source | Finding | Action |
|----------|----------|--------|---------|--------|

Add one row per finding. Use Severity values: Critical, High, Medium, or Low.
If there are no findings, add exactly one row:
| None | — | — | No issues found | — |
"""


def parse_findings_table(report: str) -> list[dict[str, str]]:
    """Parses the findings markdown table from an agent report."""
    section = report
    header_index = report.find(FINDINGS_HEADER)
    if header_index >= 0:
        section = report[header_index:]

    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0].lower() in {"severity", "---", "----------"}:
            continue
        rows.append(
            {
                "severity": cells[0],
                "location": cells[1],
                "source": cells[2],
                "finding": cells[3],
                "action": cells[4],
            }
        )
    return rows


def has_blocking_findings(findings: list[dict[str, str]]) -> bool:
    """Returns True when any finding has Critical or High severity."""
    for row in findings:
        severity = row.get("severity", "").strip().lower()
        if severity in BLOCKING_SEVERITIES:
            return True
    return False


def resolve_github_context() -> dict[str, str | None]:
    """Reads PR context from GitHub Actions environment variables."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    pr_url: str | None = None
    if event_path and Path(event_path).is_file():
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        pull_request = event.get("pull_request") or {}
        pr_url = pull_request.get("html_url")

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    base_ref = os.environ.get("GITHUB_BASE_REF") or os.environ.get("AGENT_REVIEW_BASE", "main")
    head_ref = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("AGENT_REVIEW_HEAD", "")

    return {
        "repo": repository,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "pr_url": pr_url,
    }


def run_cloud_review(
    prompt: str,
    *,
    repo: str,
    base_ref: str,
    head_ref: str,
    pr_url: str | None,
    api_key: str,
) -> str:
    """Invokes a Cursor cloud agent and returns the final report text."""
    from cursor_sdk import Agent, AgentOptions, CloudAgentOptions, CloudRepository
    from cursor_sdk.errors import CursorAgentError

    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required for cloud agent review")

    repo_url = f"https://github.com/{repo}"
    cloud_repo = CloudRepository(
        url=repo_url,
        starting_ref=head_ref or base_ref,
        pr_url=pr_url,
    )
    options = AgentOptions(
        api_key=api_key,
        model="composer-2.5",
        cloud=CloudAgentOptions(
            repos=[cloud_repo],
            work_on_current_branch=True,
            auto_create_pr=False,
        ),
    )

    try:
        result = Agent.prompt(prompt, options)
    except CursorAgentError as exc:
        raise RuntimeError(f"Cursor agent startup failed: {exc.message}") from exc

    if result.status == "error":
        raise RuntimeError(f"Cursor agent run failed: {result.id}")

    report = (result.result or "").strip()
    if not report:
        raise RuntimeError("Cursor agent returned an empty report")
    return report


def write_step_summary(report: str) -> None:
    """Appends the report to GITHUB_STEP_SUMMARY when present."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(report)
        handle.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(description="Finderscope PR agent review")
    parser.add_argument("--base", default=None, help="Base branch ref (default: GITHUB_BASE_REF or main)")
    parser.add_argument("--head", default=None, help="Head branch ref (default: GITHUB_HEAD_REF)")
    parser.add_argument("--repo", default=None, help="GitHub repo owner/name (default: GITHUB_REPOSITORY)")
    parser.add_argument(
        "--strict",
        choices=("true", "false"),
        default=os.environ.get("AGENT_REVIEW_STRICT", "false"),
        help="Strict mode: fail on Critical/High findings",
    )
    parser.add_argument(
        "--checklist",
        type=Path,
        default=DEFAULT_CHECKLIST,
        help="Path to shared checklist markdown",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write report to this file",
    )
    parser.add_argument(
        "--parse-only",
        type=Path,
        default=None,
        help="Parse an existing report file and exit (no API call)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for PR agent review."""
    args = parse_args(argv)
    strict = args.strict.lower() == "true"

    if args.parse_only:
        report = args.parse_only.read_text(encoding="utf-8")
        findings = parse_findings_table(report)
        if strict and has_blocking_findings(findings):
            return 1
        return 0

    github = resolve_github_context()
    repo = args.repo or github["repo"] or ""
    base_ref = args.base or github["base_ref"] or "main"
    head_ref = args.head or github["head_ref"] or ""
    pr_url = github["pr_url"]

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        print("CURSOR_API_KEY is not set", file=sys.stderr)
        return 1

    checklist = load_checklist(args.checklist)
    prompt = build_prompt(
        checklist,
        repo=repo,
        base_ref=base_ref,
        head_ref=head_ref,
        strict=strict,
        pr_url=pr_url,
    )

    report = run_cloud_review(
        prompt,
        repo=repo,
        base_ref=base_ref,
        head_ref=head_ref,
        pr_url=pr_url,
        api_key=api_key,
    )

    print(report)
    write_step_summary(report)

    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")

    findings = parse_findings_table(report)
    if strict and has_blocking_findings(findings):
        print("Strict mode: blocking findings detected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

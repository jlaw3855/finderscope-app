"""Tests for scripts/agent_pr_review.py findings parser."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "agent_pr_review.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("agent_pr_review", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_findings_table_empty_issues_row() -> None:
    mod = _load_module()
    report = """
## Agent review summary
- Mode: advisory

### Findings
| Severity | Location | Source | Finding | Action |
|----------|----------|--------|---------|--------|
| None | — | — | No issues found | — |
"""
    findings = mod.parse_findings_table(report)
    assert len(findings) == 1
    assert findings[0]["severity"] == "None"
    assert not mod.has_blocking_findings(findings)


def test_parse_findings_table_blocking_severities() -> None:
    mod = _load_module()
    report = """
### Findings
| Severity | Location | Source | Finding | Action |
|----------|----------|--------|---------|--------|
| Medium | app/main.py | checklist | Missing docstring | Add docstring |
| Critical | app/config.py | security | Hardcoded secret | Remove secret |
| high | frontend/App.tsx | logic | Null deref | Add guard |
"""
    findings = mod.parse_findings_table(report)
    assert len(findings) == 3
    assert mod.has_blocking_findings(findings)


def test_has_blocking_findings_only_medium() -> None:
    mod = _load_module()
    findings = [{"severity": "Medium", "location": "", "source": "", "finding": "", "action": ""}]
    assert not mod.has_blocking_findings(findings)


def test_build_prompt_includes_mode_and_branches() -> None:
    mod = _load_module()
    prompt = mod.build_prompt(
        "checklist body",
        repo="org/repo",
        base_ref="main",
        head_ref="feature",
        strict=True,
        pr_url="https://github.com/org/repo/pull/1",
    )
    assert "strict" in prompt
    assert "main" in prompt
    assert "feature" in prompt
    assert "checklist body" in prompt

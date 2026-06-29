"""Application version read from the repository VERSION file."""

from functools import lru_cache
from pathlib import Path


@lru_cache
def read_version() -> str:
    """Return the semver string from VERSION (repo root or backend root)."""
    app_root = Path(__file__).resolve().parents[1]
    for candidate in (app_root / "VERSION", app_root.parent / "VERSION"):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return "0.0.0"

"""Resolve persistent data directories for SQLite caches."""

from functools import lru_cache
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache
def get_data_dir() -> Path:
    """Return the root directory for forecast, moon, and Noctua caches."""
    from app.config import get_settings

    configured = Path(get_settings().data_dir)
    if configured.is_absolute():
        return configured
    return _backend_root() / configured


def clear_data_dir_cache() -> None:
    """Clear cached path resolution (for tests)."""
    get_data_dir.cache_clear()

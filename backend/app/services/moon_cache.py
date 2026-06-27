"""Persistent cache for FreeAstro moon enrichment data."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "moon_cache"
DB_PATH = CACHE_DIR / "moon.db"
QUOTA_PATH = CACHE_DIR / "quota.json"
SVG_DIR = CACHE_DIR / "svg"


@dataclass(frozen=True)
class CachedMoonEntry:
    date: str
    theme_key: str
    phase_name: str
    illumination_pct: float
    age_days: float | None
    is_waxing: bool | None
    special_labels: list[str]
    svg_path: str | None


@dataclass
class QuotaState:
    daily_count: int = 0
    reset_at: int | None = None
    remaining: int | None = None
    limit: int | None = None


def ensure_cache_dirs() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SVG_DIR.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    ensure_cache_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS moon_entries (
            cache_key TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            theme_key TEXT NOT NULL,
            phase_name TEXT NOT NULL,
            illumination_pct REAL NOT NULL,
            age_days REAL,
            is_waxing INTEGER,
            special_labels TEXT NOT NULL,
            svg_path TEXT,
            cached_at TEXT NOT NULL
        )
        """
    )
    return conn


def cache_key(date: str, theme_key: str, sample_profile: str = "noon") -> str:
    return f"{date}:{theme_key}:{sample_profile}"


def svg_filename(date: str, theme_key: str) -> str:
    return f"{date}_{theme_key}.svg"


def get_cached(date: str, theme_key: str, sample_profile: str = "noon") -> CachedMoonEntry | None:
    key = cache_key(date, theme_key, sample_profile)
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM moon_entries WHERE cache_key = ?",
            (key,),
        ).fetchone()

    if row is None:
        return None

    labels = json.loads(row["special_labels"])
    return CachedMoonEntry(
        date=row["date"],
        theme_key=row["theme_key"],
        phase_name=row["phase_name"],
        illumination_pct=row["illumination_pct"],
        age_days=row["age_days"],
        is_waxing=bool(row["is_waxing"]) if row["is_waxing"] is not None else None,
        special_labels=labels,
        svg_path=row["svg_path"],
    )


def store_cached(
    date: str,
    theme_key: str,
    phase_name: str,
    illumination_pct: float,
    age_days: float | None,
    is_waxing: bool | None,
    special_labels: list[str],
    svg: str | None,
    sample_profile: str = "noon",
) -> CachedMoonEntry:
    ensure_cache_dirs()
    key = cache_key(date, theme_key, sample_profile)
    svg_path: str | None = None

    if svg:
        svg_file = SVG_DIR / svg_filename(date, theme_key)
        svg_file.write_text(svg, encoding="utf-8")
        svg_path = str(svg_file)

    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO moon_entries (
                cache_key, date, theme_key, phase_name, illumination_pct,
                age_days, is_waxing, special_labels, svg_path, cached_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                date,
                theme_key,
                phase_name,
                illumination_pct,
                age_days,
                1 if is_waxing is True else 0 if is_waxing is False else None,
                json.dumps(special_labels),
                svg_path,
                datetime.now(UTC).isoformat(),
            ),
        )

    return CachedMoonEntry(
        date=date,
        theme_key=theme_key,
        phase_name=phase_name,
        illumination_pct=illumination_pct,
        age_days=age_days,
        is_waxing=is_waxing,
        special_labels=special_labels,
        svg_path=svg_path,
    )


def read_svg(date: str, theme_key: str, sample_profile: str = "noon") -> str | None:
    entry = get_cached(date, theme_key, sample_profile)
    if entry is None or entry.svg_path is None:
        return None
    path = Path(entry.svg_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_quota() -> QuotaState:
    ensure_cache_dirs()
    if not QUOTA_PATH.exists():
        return QuotaState()

    data = json.loads(QUOTA_PATH.read_text(encoding="utf-8"))
    return QuotaState(
        daily_count=int(data.get("daily_count", 0)),
        reset_at=data.get("reset_at"),
        remaining=data.get("remaining"),
        limit=data.get("limit"),
    )


def save_quota(state: QuotaState) -> None:
    ensure_cache_dirs()
    QUOTA_PATH.write_text(
        json.dumps(
            {
                "daily_count": state.daily_count,
                "reset_at": state.reset_at,
                "remaining": state.remaining,
                "limit": state.limit,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def update_quota_from_headers(headers: dict[str, str], *, increment: bool = True) -> QuotaState:
    state = load_quota()
    now = int(datetime.now(UTC).timestamp())

    reset_raw = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
    if reset_raw is not None:
        try:
            reset_at = int(reset_raw)
            if state.reset_at is not None and now >= state.reset_at:
                state.daily_count = 0
            state.reset_at = reset_at
        except ValueError:
            pass

    limit_raw = headers.get("X-RateLimit-Limit") or headers.get("x-ratelimit-limit")
    if limit_raw is not None:
        try:
            state.limit = int(limit_raw)
        except ValueError:
            pass

    remaining_raw = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
    if remaining_raw is not None:
        try:
            state.remaining = int(remaining_raw)
        except ValueError:
            pass

    if increment:
        state.daily_count += 1

    save_quota(state)
    return state


def quota_available(state: QuotaState | None = None) -> bool:
    state = state or load_quota()
    if state.remaining is not None and state.remaining <= 0:
        return False
    if state.limit is not None and state.daily_count >= state.limit:
        return False
    if state.daily_count >= 80:
        return False
    return True

"""Permanent SQLite cache for NoctuaSky skysource responses."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.data_paths import get_data_dir


def _cache_dir() -> Path:
    return get_data_dir() / "noctua_cache"


def _db_path() -> Path:
    return _cache_dir() / "noctua.db"

def normalize_lookup_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def cache_key(lookup: str) -> str:
    return f"skysource:{normalize_lookup_key(lookup)}"


def ensure_cache_dirs() -> None:
    _cache_dir().mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    ensure_cache_dirs()
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skysource_entries (
            cache_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            cached_at TEXT NOT NULL
        )
        """
    )
    return conn


def get_cached(lookup: str) -> dict | None:
    key = cache_key(lookup)
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM skysource_entries WHERE cache_key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def store_cached(lookup: str, payload: dict) -> None:
    key = cache_key(lookup)
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO skysource_entries (
                cache_key, payload_json, cached_at
            ) VALUES (?, ?, ?)
            """,
            (key, json.dumps(payload), datetime.now(UTC).isoformat()),
        )

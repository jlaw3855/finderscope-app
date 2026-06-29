"""SQLite cache for forecast upstream API responses."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "forecast_cache"
DB_PATH = CACHE_DIR / "forecast.db"

LAYER_GEOCODE = "geocode"
LAYER_ASTRONOMY = "astronomy"
LAYER_WEATHER = "weather"
LAYER_ASTRO = "astro"


def normalize_coord(value: float) -> float:
    return round(value, 4)


def geocode_cache_key(address: str) -> str:
    normalized = " ".join(address.strip().lower().split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"geocode:{digest[:32]}"


def astronomy_cache_key(
    latitude: float,
    longitude: float,
    date_start: str,
    date_end: str,
) -> str:
    lat = normalize_coord(latitude)
    lon = normalize_coord(longitude)
    return f"astronomy:{lat}:{lon}:{date_start}:{date_end}"


def weather_cache_key(
    latitude: float,
    longitude: float,
    forecast_start: str,
    forecast_days: int,
) -> str:
    lat = normalize_coord(latitude)
    lon = normalize_coord(longitude)
    return f"weather:{lat}:{lon}:{forecast_start}:{forecast_days}"


def astro_cache_key(latitude: float, longitude: float) -> str:
    lat = normalize_coord(latitude)
    lon = normalize_coord(longitude)
    return f"astro:{lat}:{lon}"


def ensure_cache_dirs() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast_entries (
            cache_key TEXT PRIMARY KEY,
            layer TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            cached_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_forecast_entries_expires_at ON forecast_entries(expires_at)"
    )


def _connect() -> sqlite3.Connection:
    ensure_cache_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _expires_at(hours: float) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def purge_expired_entries(*, conn: sqlite3.Connection | None = None) -> int:
    now = datetime.now(UTC).isoformat()
    if conn is not None:
        cursor = conn.execute(
            "DELETE FROM forecast_entries WHERE expires_at <= ?",
            (now,),
        )
        return cursor.rowcount

    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM forecast_entries WHERE expires_at <= ?",
            (now,),
        )
        return cursor.rowcount


def get_cached_entry(cache_key: str) -> dict | None:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT payload_json FROM forecast_entries
            WHERE cache_key = ? AND expires_at > ?
            """,
            (cache_key, now),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def store_cached_entry(
    cache_key: str,
    layer: str,
    payload: dict,
    *,
    ttl_hours: float,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO forecast_entries (
                cache_key, layer, payload_json, cached_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                cache_key,
                layer,
                json.dumps(payload),
                datetime.now(UTC).isoformat(),
                _expires_at(ttl_hours),
            ),
        )
        purge_expired_entries(conn=conn)

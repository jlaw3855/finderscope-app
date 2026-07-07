"""Application configuration loaded from environment variables."""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_ROOT / ".env"
_INVISIBLE_CHARS = "\ufeff\u200b"
_IPGEOLOCATION_ENV_KEY = "IPGEOLOCATION_API_KEY"

KeySource = Literal["environment", "env_file", "unknown"]


def sanitize_api_key(value: str) -> str:
    """Normalizes API keys loaded from .env files (BOM, CRLF, quotes, whitespace)."""
    cleaned = value
    for char in _INVISIBLE_CHARS:
        cleaned = cleaned.replace(char, "")
    cleaned = cleaned.replace("\r", "")
    cleaned = cleaned.replace("\n", "")
    cleaned = cleaned.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
        cleaned = cleaned[1:-1].strip()
    return cleaned.strip()


def _key_has_internal_whitespace(value: str) -> bool:
    return any(char.isspace() for char in value)


def describe_api_key_health(value: str, *, source: KeySource = "unknown") -> dict[str, bool | int | str]:
    """Returns safe metadata about an API key without exposing its value."""
    cleaned = sanitize_api_key(value)
    stripped = value
    for char in _INVISIBLE_CHARS:
        stripped = stripped.replace(char, "")
    stripped = stripped.strip()
    return {
        "length": len(cleaned),
        "empty": len(cleaned) == 0,
        "had_bom": "\ufeff" in value,
        "had_cr": "\r" in value,
        "had_zero_width": "\u200b" in value,
        "had_internal_whitespace": _key_has_internal_whitespace(cleaned),
        "had_surrounding_quotes": (
            len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "'\""
        ),
        "source": source,
    }


def _parse_env_file_value(key: str) -> str | None:
    """Reads a single key from backend/.env without using pydantic."""
    if not _ENV_FILE.is_file():
        return None

    prefix = f"{key}="
    for line in _ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(prefix):
            return stripped[len(prefix) :]
    return None


def _env_file_defines_non_empty_key(key: str) -> bool:
    raw = _parse_env_file_value(key)
    return raw is not None and sanitize_api_key(raw) != ""


def get_ipgeolocation_key_source() -> KeySource:
    """Reports whether IPGEOLOCATION_API_KEY came from the OS env or backend/.env."""
    if os.environ.get(_IPGEOLOCATION_ENV_KEY) is not None:
        return "environment"
    if _parse_env_file_value(_IPGEOLOCATION_ENV_KEY) is not None:
        return "env_file"
    return "unknown"


def get_ipgeolocation_key_raw() -> tuple[str, KeySource]:
    """Returns the raw key value and its source before pydantic normalization."""
    source = get_ipgeolocation_key_source()
    if source == "environment":
        return os.environ[_IPGEOLOCATION_ENV_KEY], source
    if source == "env_file":
        raw = _parse_env_file_value(_IPGEOLOCATION_ENV_KEY)
        return raw or "", source
    return "", "unknown"


def check_env_file_encoding() -> str | None:
    """Returns a warning message when backend/.env has a non-UTF-8 encoding."""
    if not _ENV_FILE.is_file():
        return None

    raw_bytes = _ENV_FILE.read_bytes()
    if raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
        return (
            "backend/.env appears to be UTF-16. Re-save as UTF-8 "
            "(VS Code/Cursor: Save with Encoding -> UTF-8)."
        )
    try:
        raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return "backend/.env is not valid UTF-8. Re-save as UTF-8."
    return None


class Settings(BaseSettings):
    """Server-side settings. API keys must never be exposed to the frontend."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    ipgeolocation_api_key: str
    cors_origins: str = "http://localhost:5173"
    freeastro_api_key: str = ""
    moon_enrichment_enabled: bool = True
    moon_visual_moon_color: str = "#E0E0E0"
    moon_visual_shadow_color: str = "#1a2030"
    forecast_cache_enabled: bool = True
    forecast_geocode_ttl_hours: float = 24 * 30
    forecast_astronomy_ttl_hours: float = 24
    forecast_weather_ttl_hours: float = 3
    seventimer_enabled: bool = True
    forecast_astro_ttl_hours: float = 3
    seventimer_altitude_correction: int = 0
    noctua_enrichment_enabled: bool = False
    noctua_base_url: str = "https://api.noctuasky.com/api/v1"
    noctua_request_timeout_seconds: float = 12.0
    noctua_enrichment_budget_seconds: float = 5.0
    nasa_api_key: str = "DEMO_KEY"
    data_dir: str = "data"
    serve_static: bool = False
    static_dir: str = "static"
    http_trust_env: bool = True

    @field_validator(
        "ipgeolocation_api_key",
        "freeastro_api_key",
        "nasa_api_key",
        mode="before",
    )
    @classmethod
    def normalize_api_keys(cls, value: object) -> object:
        if isinstance(value, str):
            return sanitize_api_key(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def static_dir_path(self) -> Path:
        configured = Path(self.static_dir)
        if configured.is_absolute():
            return configured
        return _BACKEND_ROOT / configured


def log_ipgeolocation_key_warnings() -> None:
    """Logs safe startup warnings for IPGeolocation key loading issues."""
    encoding_warning = check_env_file_encoding()
    if encoding_warning:
        logger.warning(encoding_warning)

    raw_value, source = get_ipgeolocation_key_raw()
    health = describe_api_key_health(raw_value, source=source)

    if health["empty"]:
        logger.warning(
            "IPGEOLOCATION_API_KEY is empty. Set it in backend/.env for forecast geocode and astronomy."
        )

    corruption_flags = [
        name
        for name, had_issue in (
            ("BOM", health["had_bom"]),
            ("CR", health["had_cr"]),
            ("zero-width chars", health["had_zero_width"]),
            ("internal whitespace", health["had_internal_whitespace"]),
            ("surrounding quotes", health["had_surrounding_quotes"]),
        )
        if had_issue
    ]
    if corruption_flags and not health["empty"]:
        logger.warning(
            "IPGEOLOCATION_API_KEY had formatting issues (%s) that were auto-corrected.",
            ", ".join(corruption_flags),
        )

    if source == "environment" and _env_file_defines_non_empty_key(_IPGEOLOCATION_ENV_KEY):
        logger.warning(
            "OS environment variable IPGEOLOCATION_API_KEY overrides backend/.env. "
            "Unset the system/shell variable or update it "
            "(Windows: Remove-Item Env:IPGEOLOCATION_API_KEY)."
        )

    if os.environ.get("FINDERSCOPE_DEBUG_CONFIG") == "1":
        logger.info("IPGEOLOCATION_API_KEY health: %s", health)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Clears cached settings (for tests or after .env changes in long-lived processes)."""
    get_settings.cache_clear()

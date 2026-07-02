"""Tests for settings loading and API key normalization."""

from pathlib import Path

import pytest
from app.config import (
    _ENV_FILE,
    Settings,
    check_env_file_encoding,
    describe_api_key_health,
    get_ipgeolocation_key_source,
    sanitize_api_key,
)


def test_env_file_resolves_to_backend_directory() -> None:
    assert _ENV_FILE == Path(__file__).resolve().parents[1] / ".env"


def test_sanitize_api_key_strips_bom_crlf_and_quotes() -> None:
    assert sanitize_api_key("\ufeffabc123\r\n") == "abc123"
    assert sanitize_api_key('  "abc123"  ') == "abc123"
    assert sanitize_api_key("'abc123'\r") == "abc123"


def test_sanitize_api_key_strips_cr_anywhere() -> None:
    assert sanitize_api_key("ab\r\nc123") == "abc123"
    assert sanitize_api_key("ab\rc123") == "abc123"


def test_sanitize_api_key_strips_zero_width_chars() -> None:
    assert sanitize_api_key("ab\u200bc123") == "abc123"


def test_settings_normalizes_ipgeolocation_api_key() -> None:
    settings = Settings(ipgeolocation_api_key="\ufeffmy-key\r")
    assert settings.ipgeolocation_api_key == "my-key"


def test_describe_api_key_health_flags_without_exposing_value() -> None:
    health = describe_api_key_health('\ufeff"key with space"\r\n', source="env_file")

    assert health["length"] == len("key with space")
    assert health["empty"] is False
    assert health["had_bom"] is True
    assert health["had_cr"] is True
    assert health["had_surrounding_quotes"] is True
    assert health["had_internal_whitespace"] is True
    assert health["source"] == "env_file"


def test_describe_api_key_health_empty_key() -> None:
    health = describe_api_key_health("  \r\n  ", source="unknown")

    assert health["empty"] is True
    assert health["length"] == 0


def test_env_var_overrides_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("IPGEOLOCATION_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "env-key")

    settings = Settings(_env_file=env_file)

    assert settings.ipgeolocation_api_key == "env-key"


def test_get_ipgeolocation_key_source_prefers_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "from-env")

    assert get_ipgeolocation_key_source() == "environment"


def test_check_env_file_encoding_detects_utf16(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"\xff\xfe" + "IPGEOLOCATION_API_KEY=test\r\n".encode("utf-16-le"))
    monkeypatch.setattr("app.config._ENV_FILE", env_file)

    warning = check_env_file_encoding()

    assert warning is not None
    assert "UTF-16" in warning


def test_check_env_file_encoding_accepts_utf8(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("IPGEOLOCATION_API_KEY=test\n", encoding="utf-8")
    monkeypatch.setattr("app.config._ENV_FILE", env_file)

    assert check_env_file_encoding() is None

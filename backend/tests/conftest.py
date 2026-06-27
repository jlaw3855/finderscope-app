"""Shared pytest fixtures for Finderscope backend tests."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLACEHOLDER_VALUES = {"your_key", "your_id", "your_secret", ""}


def _live_tests_enabled() -> bool:
    if os.getenv("FINDERSCOPE_LIVE_TESTS") != "1":
        return False

    try:
        settings = Settings()
    except ValidationError:
        return False

    return all(
        [
            settings.ipgeolocation_api_key not in PLACEHOLDER_VALUES,
        ]
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: hits real external APIs; requires backend/.env keys and FINDERSCOPE_LIVE_TESTS=1",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _live_tests_enabled():
        return

    reason = "Set FINDERSCOPE_LIVE_TESTS=1 with valid backend/.env keys to run live tests"
    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture
def fake_settings() -> Settings:
    return Settings(
        ipgeolocation_api_key="test-ipgeo-key",
        cors_origins="http://localhost:5173",
        forecast_cache_enabled=False,
        noctua_enrichment_enabled=False,
    )


@pytest.fixture
def client(fake_settings: Settings) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: fake_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def load_fixture():
    def _load(name: str) -> dict:
        path = FIXTURES_DIR / name
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    return _load

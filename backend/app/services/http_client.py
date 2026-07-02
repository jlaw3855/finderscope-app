"""Shared httpx AsyncClient for upstream API calls."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client is not initialized; ensure app lifespan is active.")
    return _client


async def init_http_client() -> None:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@asynccontextmanager
async def http_client_lifespan() -> AsyncIterator[None]:
    await init_http_client()
    try:
        yield
    finally:
        await close_http_client()

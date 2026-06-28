"""NoctuaSky skysource API client."""

from __future__ import annotations

import httpx

from app.config import Settings
from app.services.http_client import get_http_client
from app.services import noctua_cache

BASE_URL = "https://api.noctuasky.com/api/v1"


class NoctuaError(Exception):
    """Raised when the NoctuaSky API returns an error."""


async def fetch_skysource_by_name(settings: Settings, name: str) -> dict | None:
    """Fetch one skysource by exact name; returns None on miss or error."""
    cached = noctua_cache.get_cached(name)
    if cached is not None:
        return cached

    url = f"{settings.noctua_base_url.rstrip('/')}/skysources/name/{name}"
    try:
        response = await get_http_client().get(
            url,
            timeout=settings.noctua_request_timeout_seconds,
        )
    except httpx.HTTPError:
        return None

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        return None

    payload = response.json()
    noctua_cache.store_cached(name, payload)
    return payload


async def search_skysources(settings: Settings, query: str, *, limit: int = 3) -> list[dict]:
    """Search skysources; returns empty list on error."""
    cache_lookup = f"search:{query}:{limit}"
    cached = noctua_cache.get_cached(cache_lookup)
    if cached is not None:
        return cached.get("results", [])

    url = f"{settings.noctua_base_url.rstrip('/')}/skysources/"
    params = {"q": query, "limit": limit}
    try:
        response = await get_http_client().get(
            url,
            params=params,
            timeout=settings.noctua_request_timeout_seconds,
        )
    except httpx.HTTPError:
        return []

    if response.status_code >= 400:
        return []

    results = response.json()
    if not isinstance(results, list):
        return []

    noctua_cache.store_cached(cache_lookup, {"results": results})
    return results

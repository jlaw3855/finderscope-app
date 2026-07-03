"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings, log_ipgeolocation_key_warnings
from app.routers import apod, astronomy, dso_visibility, forecast, moon_enrichment
from app.services.http_client import close_http_client, init_http_client
from app.version import read_version

settings = get_settings()
APP_VERSION = read_version()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_ipgeolocation_key_warnings()
    await init_http_client()
    try:
        yield
    finally:
        await close_http_client()


app = FastAPI(
    title="Finderscope API",
    description="Server-side proxy for stargazing weather and astronomy summaries.",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router)
app.include_router(moon_enrichment.router)
app.include_router(astronomy.router)
app.include_router(apod.router)
if settings.dso_visibility_enabled:
    app.include_router(dso_visibility.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


if settings.serve_static:
    static_root = settings.static_dir_path
    if static_root.is_dir():
        app.mount("/", StaticFiles(directory=static_root, html=True), name="spa")

"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import apod, astronomy, forecast, moon_enrichment
from app.services.http_client import close_http_client, init_http_client

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_http_client()
    try:
        yield
    finally:
        await close_http_client()


app = FastAPI(
    title="Finderscope API",
    description="Server-side proxy for stargazing weather and astronomy summaries.",
    version="1.0.0",
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

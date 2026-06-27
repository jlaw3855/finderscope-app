"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import astronomy, forecast, moon_enrichment

settings = get_settings()

app = FastAPI(
    title="Finderscope API",
    description="Server-side proxy for stargazing weather and astronomy summaries.",
    version="1.0.0",
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

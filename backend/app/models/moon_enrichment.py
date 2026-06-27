"""Pydantic schemas for FreeAstro moon enrichment API."""

from typing import Literal

from pydantic import BaseModel, Field


class MoonEnrichmentEntry(BaseModel):
    date: str
    phase_name: str
    illumination_pct: float
    age_days: float | None = None
    is_waxing: bool | None = None
    special_labels: list[str] = Field(default_factory=list)
    visual_url: str | None = None


MoonEnrichmentStatus = Literal["complete", "partial", "pending", "unavailable"]


class MoonEnrichmentResponse(BaseModel):
    entries: list[MoonEnrichmentEntry]
    status: MoonEnrichmentStatus
    cached_count: int
    pending_dates: list[str] = Field(default_factory=list)

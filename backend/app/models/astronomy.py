"""Pydantic schemas for the astronomy summary API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AstronomyEventCategory = Literal[
    "lunar_eclipse",
    "solar_eclipse",
    "transit",
    "conjunction",
    "opposition",
]


class AstronomyRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str = Field(..., min_length=1)
    dates: list[str] = Field(..., min_length=1, max_length=7)


class AstronomyEvent(BaseModel):
    id: str
    category: AstronomyEventCategory
    title: str
    start_at: datetime
    peak_at: datetime | None = None
    end_at: datetime | None = None
    description: str
    visible_locally: bool = True


class VisibilityWindow(BaseModel):
    start: str
    end: str


class PlanetVisibilityRow(BaseModel):
    body: str
    visible: bool
    windows: list[VisibilityWindow]
    peak_altitude_deg: float | None = None
    peak_at: str | None = None
    magnitude: float | None = None


class PlanetDayVisibility(BaseModel):
    date: str
    planets: list[PlanetVisibilityRow]


class AstronomyResponse(BaseModel):
    events: list[AstronomyEvent]
    planet_visibility: list[PlanetDayVisibility]

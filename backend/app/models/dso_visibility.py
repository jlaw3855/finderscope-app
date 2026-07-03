"""Pydantic schemas for the DSO visibility API."""

from pydantic import BaseModel, Field

from app.models.astronomy import VisibilityWindow


class DsoVisibilityRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str = Field(..., min_length=1)
    dates: list[str] = Field(..., min_length=1, max_length=7)


class SiteSkyConditions(BaseModel):
    bortle: int
    sqm: float
    limiting_magnitude: float
    source: str


class DsoVisibilityRow(BaseModel):
    id: str
    name: str
    common_name: str | None = None
    object_type: str
    visible: bool
    windows_astronomical: list[VisibilityWindow] = Field(default_factory=list)
    peak_altitude_deg: float | None = None
    peak_at: str | None = None
    magnitude: float | None = None
    contrast: float
    visibility_score: float


class DsoDayVisibility(BaseModel):
    date: str
    objects: list[DsoVisibilityRow]


class DsoVisibilityResponse(BaseModel):
    site_sky: SiteSkyConditions
    dso_visibility: list[DsoDayVisibility]

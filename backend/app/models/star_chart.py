"""Pydantic schemas for the star chart API."""

from typing import Literal

from pydantic import BaseModel, Field


class StarChartRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    view_type: Literal["all-sky", "constellation"] = "all-sky"
    constellation: str | None = Field(default=None, min_length=3, max_length=3)


class StarChartResponse(BaseModel):
    image_url: str
    view_type: str

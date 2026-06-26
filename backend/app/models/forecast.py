"""Pydantic schemas for the forecast API."""

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    address: str = Field(..., min_length=1, max_length=500)


class LocationInfo(BaseModel):
    label: str
    latitude: float
    longitude: float
    timezone: str


class TimeWindow(BaseModel):
    start: str
    end: str


class BestHourWindow(BaseModel):
    start: str
    end: str
    score: int


class CloudCoverBreakdown(BaseModel):
    total: float | None = None
    low: float | None = None
    mid: float | None = None
    high: float | None = None


class PrecipitationBreakdown(BaseModel):
    total_mm: float | None = None
    max_hourly_mm: float | None = None
    max_probability: float | None = None


class HourlyScore(BaseModel):
    time: str
    at: str
    score: int
    cloud_cover: float | None = None
    cloud_cover_low: float | None = None
    cloud_cover_mid: float | None = None
    cloud_cover_high: float | None = None
    visibility: float | None = None
    precipitation: float | None = None
    precipitation_probability: float | None = None
    dew_point: float | None = None
    temperature: float | None = None


class NightForecast(BaseModel):
    date: str
    rating: str
    score: int | None
    moon_phase: str
    moon_illumination: float
    temperature_high: float | None = None
    temperature_low: float | None = None
    cloud_cover: CloudCoverBreakdown = Field(default_factory=CloudCoverBreakdown)
    precipitation: PrecipitationBreakdown = Field(default_factory=PrecipitationBreakdown)
    dark_window: TimeWindow | None = None
    best_hours: list[BestHourWindow] = Field(default_factory=list)
    hourly: list[HourlyScore] = Field(default_factory=list)
    no_darkness: bool = False


class ForecastResponse(BaseModel):
    location: LocationInfo
    nights: list[NightForecast]

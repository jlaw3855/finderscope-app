"""Pydantic schemas for NASA APOD proxy responses."""

from typing import Literal

from pydantic import BaseModel


class ApodResponse(BaseModel):
    title: str
    date: str
    explanation: str
    media_type: Literal["image", "video"]
    image_url: str | None = None
    video_url: str | None = None
    copyright: str | None = None

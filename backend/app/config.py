"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side settings. API keys must never be exposed to the frontend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ipgeolocation_api_key: str
    cors_origins: str = "http://localhost:5173"
    freeastro_api_key: str = ""
    moon_enrichment_enabled: bool = True
    moon_visual_moon_color: str = "#E0E0E0"
    moon_visual_shadow_color: str = "#1a2030"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

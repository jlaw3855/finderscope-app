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
    forecast_cache_enabled: bool = True
    forecast_geocode_ttl_hours: float = 24 * 30
    forecast_astronomy_ttl_hours: float = 24
    forecast_weather_ttl_hours: float = 3
    seventimer_enabled: bool = True
    forecast_astro_ttl_hours: float = 3
    seventimer_altitude_correction: int = 0
    noctua_enrichment_enabled: bool = False
    noctua_base_url: str = "https://api.noctuasky.com/api/v1"
    noctua_request_timeout_seconds: float = 12.0
    noctua_enrichment_budget_seconds: float = 5.0
    nasa_api_key: str = "DEMO_KEY"
    data_dir: str = "data"
    serve_static: bool = False
    static_dir: str = "static"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def static_dir_path(self) -> "Path":
        from pathlib import Path

        configured = Path(self.static_dir)
        if configured.is_absolute():
            return configured
        return Path(__file__).resolve().parents[1] / configured


@lru_cache
def get_settings() -> Settings:
    return Settings()

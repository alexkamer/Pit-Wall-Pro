from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "F1 WebApp API"
    app_version: str = "0.1.0"

    # API Configuration
    espn_api_base_url: str = "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1"

    # FastF1 Configuration
    fastf1_cache_enabled: bool = True
    fastf1_cache_dir: str = "./cache/fastf1"

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Cache TTL (seconds)
    cache_ttl_schedule: int = 3600  # 1 hour
    cache_ttl_standings: int = 300  # 5 minutes
    cache_ttl_live_timing: int = 10  # 10 seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

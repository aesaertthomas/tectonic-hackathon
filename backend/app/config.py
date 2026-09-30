from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./timemachine.db"
    debug: bool = False
    cookie_secure: bool = False
    session_ttl_hours: int = Field(default=8, ge=1, le=24)
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    demo_password: str = ""
    frontend_dist: str = str(REPO_ROOT / "frontend" / "dist")


@lru_cache
def get_settings() -> Settings:
    return Settings()

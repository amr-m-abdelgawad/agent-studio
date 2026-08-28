from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://studio:studio@localhost:5432/studio"
    session_secret: str = "dev-session-secret-change-me"
    studio_org_name: str = ""
    bootstrap_owner_email: str = ""
    bootstrap_owner_password: str = ""
    studio_cookie_secure: bool = False
    invite_ttl_hours: int = 168
    studio_email_adapter: str = "dev"

    temporal_host: str = "temporal:7233"
    temporal_namespace: str = "studio-dev"
    temporal_task_queue: str = "studio-default"

    api_host: str = "0.0.0.0"
    api_port: int = 8080


@lru_cache
def get_settings() -> Settings:
    return Settings()

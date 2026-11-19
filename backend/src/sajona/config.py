"""Configuración centralizada basada en variables de entorno."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de ejecución de SAJONA Backend."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SAJONA API"
    app_version: str = "1.0.0"
    environment: str = "production"
    database_url: str = "postgresql+asyncpg://sajona:sajona_pass@sajona-db:5432/sajona"
    jwt_secret_key: str = "change-this-in-production-min-32-chars-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    audit_log_dir: str = "/app/audit_logs"
    seed_demo_data: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:8088"


@lru_cache
def get_settings() -> Settings:
    """Retorna instancia cacheada de configuración."""
    return Settings()

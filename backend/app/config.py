"""Application settings, read from environment variables (and an optional .env file).

No secrets have defaults: a missing POSTGRES_PASSWORD fails at startup instead of
silently using a guessable value.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _REPO_ROOT / "backend" / ".env"),
        extra="ignore",
    )

    # Database
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    db_connect_timeout_seconds: int = 5
    db_pool_size: int = 5
    db_max_overflow: int = 5

    # Triage
    triage_provider: Literal["llm", "ollama", "rules", "simulated"] = "rules"
    simulated_seed: int = 0
    simulated_failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

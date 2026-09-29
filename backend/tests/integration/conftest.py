from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from alembic import command
from app.config import get_settings
from app.db import get_engine
from app.deps import get_triage_provider
from app.main import app
from app.providers.triage.simulated import SimulatedTriage

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


def _ensure_test_database() -> None:
    settings = get_settings()
    admin = create_engine(
        settings.database_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": settings.postgres_db}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{settings.postgres_db}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    _ensure_test_database()
    command.upgrade(alembic_config(), "head")


@pytest.fixture(autouse=True)
def _clean_tables(_database: None) -> None:
    with get_engine().begin() as conn:
        conn.execute(text("TRUNCATE TABLE complaints"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_triage_provider] = lambda: SimulatedTriage()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

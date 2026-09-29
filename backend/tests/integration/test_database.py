import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.db import get_engine
from app.models import Base
from tests.integration.conftest import alembic_config

INSERT = """
INSERT INTO complaints (text, location, category, priority, triaged_by, triage_latency_ms)
VALUES (:text, :location, 'water', 'high', :triaged_by, :latency)
"""
GOOD = {
    "text": "Burst water main flooding the street",
    "location": "Street 12",
    "triaged_by": "rules",
    "latency": 3,
}


def test_models_match_the_migrations() -> None:
    with get_engine().connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


@pytest.mark.parametrize(
    "bad",
    [
        {"text": "too short"},
        {"text": "x" * 2001},
        {"location": "ab"},
        {"triaged_by": "made-up-provider"},
        {"latency": -1},
    ],
)
def test_database_enforces_constraints_itself(bad: dict[str, object]) -> None:
    with pytest.raises(IntegrityError), get_engine().begin() as conn:
        conn.execute(text(INSERT), {**GOOD, **bad})


def test_valid_row_gets_server_generated_defaults() -> None:
    with get_engine().begin() as conn:
        conn.execute(text(INSERT), GOOD)
        row = conn.execute(text("SELECT id, status, created_at, updated_at FROM complaints")).one()
    assert row.id is not None and row.status == "open"
    assert row.created_at.tzinfo is not None and row.updated_at.tzinfo is not None


def test_migration_is_reversible() -> None:
    config = alembic_config()
    command.downgrade(config, "base")
    with get_engine().connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.complaints')")).scalar() is None
    command.upgrade(config, "head")
    with get_engine().connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.complaints')")).scalar() is not None

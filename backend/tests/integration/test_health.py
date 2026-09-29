from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.deps import get_db_session, get_readiness_service
from app.main import app
from app.repositories.health_repository import HealthRepository
from app.services.readiness_service import ReadinessService


def _broken_session() -> Iterator[Session]:
    raise RuntimeError("the database must not be touched")
    yield  # pragma: no cover


def test_health_does_not_touch_the_database(client: TestClient) -> None:
    app.dependency_overrides[get_db_session] = _broken_session
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_is_200_when_postgres_is_reachable(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"postgres": "ok"}, "failed": []}


def test_ready_is_503_naming_the_failed_dependency(client: TestClient) -> None:
    def failing() -> None:
        raise ConnectionError("down")

    app.dependency_overrides[get_readiness_service] = lambda: ReadinessService(
        {"postgres": failing}
    )
    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["failed"] == ["postgres"]


@pytest.mark.filterwarnings("ignore")
def test_ready_is_503_when_postgres_is_really_unreachable(client: TestClient) -> None:
    dead_engine = create_engine(
        "postgresql+psycopg://nobody:nothing@127.0.0.1:1/none", connect_args={"connect_timeout": 1}
    )
    session = Session(bind=dead_engine)
    app.dependency_overrides[get_readiness_service] = lambda: ReadinessService(
        {"postgres": HealthRepository(session).ping}
    )
    response = client.get("/ready")
    session.close()
    assert response.status_code == 503
    assert response.json()["failed"] == ["postgres"]

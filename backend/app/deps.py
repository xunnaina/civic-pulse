"""Dependency wiring: builds the object graph (session -> repository -> service) per request."""

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker
from app.providers.triage.base import TriageProvider
from app.providers.triage.factory import build_triage_provider
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.health_repository import HealthRepository
from app.services.complaint_service import ComplaintService
from app.services.readiness_service import ReadinessService
from app.services.triage_service import TriageService


def get_db_session() -> Iterator[Session]:
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


@lru_cache
def _provider_singleton() -> TriageProvider:
    return build_triage_provider(get_settings())


def get_triage_provider() -> TriageProvider:
    """Overridden in tests via app.dependency_overrides."""
    return _provider_singleton()


SessionDep = Annotated[Session, Depends(get_db_session)]
ProviderDep = Annotated[TriageProvider, Depends(get_triage_provider)]


def get_complaint_service(session: SessionDep, provider: ProviderDep) -> ComplaintService:
    return ComplaintService(ComplaintRepository(session), TriageService(provider))


def get_readiness_service(session: SessionDep) -> ReadinessService:
    return ReadinessService({"postgres": HealthRepository(session).ping})

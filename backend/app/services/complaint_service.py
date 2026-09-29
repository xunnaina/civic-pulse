"""Business rules for complaints: triage on create, state machine on status change."""

import logging
import uuid
from collections.abc import Sequence

from app.models.complaint import Complaint
from app.models.enums import Category, Priority, Status
from app.repositories.complaint_repository import ComplaintRepository
from app.services.errors import ComplaintNotFoundError
from app.services.state_machine import assert_transition
from app.services.triage_service import TriageService

logger = logging.getLogger(__name__)


class ComplaintService:
    def __init__(self, repo: ComplaintRepository, triage: TriageService) -> None:
        self._repo = repo
        self._triage = triage

    def create(self, *, text: str, location: str, reporter_contact: str | None) -> Complaint:
        outcome = self._triage.triage(text, location)
        complaint = self._repo.add(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=outcome.result.category,
            priority=outcome.result.priority,
            ai_summary=outcome.result.summary,
            triaged_by=outcome.triaged_by,
            triage_latency_ms=outcome.latency_ms,
        )
        self._repo.commit()
        if outcome.fallback_error is not None:
            logger.warning(
                "triage fallback used",
                extra={
                    "complaint_id": str(complaint.id),
                    "provider": self._triage.provider_name,
                    "error_class": outcome.fallback_error,
                },
            )
        return complaint

    def get(self, complaint_id: uuid.UUID) -> Complaint:
        complaint = self._repo.get(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(str(complaint_id))
        return complaint

    def list_complaints(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        page: int,
        page_size: int,
    ) -> tuple[Sequence[Complaint], int]:
        return self._repo.list_page(
            category=category,
            priority=priority,
            status=status,
            offset=(page - 1) * page_size,
            limit=page_size,
        )

    def change_status(self, complaint_id: uuid.UUID, target: Status) -> Complaint:
        complaint = self._repo.get_for_update(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(str(complaint_id))
        assert_transition(complaint.status, target)
        self._repo.set_status(complaint, target)
        self._repo.commit()
        return complaint

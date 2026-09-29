"""All SQL for complaints lives here (and nowhere else)."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.enums import Category, Priority, Status


class ComplaintRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        text: str,
        location: str,
        reporter_contact: str | None,
        category: Category,
        priority: Priority,
        ai_summary: str | None,
        triaged_by: str,
        triage_latency_ms: int,
    ) -> Complaint:
        row = Complaint(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=category,
            priority=priority,
            ai_summary=ai_summary,
            triaged_by=triaged_by,
            triage_latency_ms=triage_latency_ms,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return row

    def get(self, complaint_id: uuid.UUID) -> Complaint | None:
        return self._session.get(Complaint, complaint_id)

    def get_for_update(self, complaint_id: uuid.UUID) -> Complaint | None:
        """Fetch and row-lock a complaint so concurrent status changes cannot interleave."""
        stmt = (
            select(Complaint)
            .where(Complaint.id == complaint_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_page(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Complaint], int]:
        filters = []
        if category is not None:
            filters.append(Complaint.category == category)
        if priority is not None:
            filters.append(Complaint.priority == priority)
        if status is not None:
            filters.append(Complaint.status == status)

        count_stmt = select(func.count()).select_from(Complaint).where(*filters)
        total = self._session.execute(count_stmt).scalar_one()

        page_stmt = (
            select(Complaint)
            .where(*filters)
            .order_by(Complaint.created_at.desc(), Complaint.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = self._session.execute(page_stmt).scalars().all()
        return items, total

    def set_status(self, complaint: Complaint, status: Status) -> Complaint:
        complaint.status = status
        self._session.flush()
        self._session.refresh(complaint)  # picks up the new updated_at
        return complaint

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

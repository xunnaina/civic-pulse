import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Category, Priority, Status

# Values allowed in complaints.triaged_by ("simulated" is used only by SimulatedTriage in CI).
TRIAGED_BY_VALUES = ("llm:groq", "llm:ollama", "rules", "rules:fallback", "simulated")


def _enum(enum_cls: type[Category] | type[Priority] | type[Status], name: str) -> sa.Enum:
    """Native PostgreSQL enum whose labels are the lowercase values."""
    return sa.Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        sa.CheckConstraint(
            "char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"
        ),
        sa.CheckConstraint(
            "char_length(location) BETWEEN 3 AND 200", name="ck_complaints_location_length"
        ),
        sa.CheckConstraint(
            "triaged_by IN ('llm:groq', 'llm:ollama', 'rules', 'rules:fallback', 'simulated')",
            name="ck_complaints_triaged_by",
        ),
        sa.CheckConstraint("triage_latency_ms >= 0", name="ck_complaints_triage_latency_nonneg"),
        # Serves the dashboard list/stats queries: WHERE status = ? [AND priority = ?] and
        # GROUP BY status/priority.
        sa.Index("ix_complaints_status_priority", "status", "priority"),
        # Serves ORDER BY created_at DESC (dashboard pagination, newest-first listings).
        sa.Index("ix_complaints_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    location: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    category: Mapped[Category] = mapped_column(_enum(Category, "complaint_category"))
    priority: Mapped[Priority] = mapped_column(_enum(Priority, "complaint_priority"))
    status: Mapped[Status] = mapped_column(
        _enum(Status, "complaint_status"), server_default=Status.OPEN.value
    )
    ai_summary: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

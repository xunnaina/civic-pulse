"""create complaints table

Revision ID: 0001
Revises:
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORY_VALUES = ("water", "electricity", "sanitation", "roads", "streetlights", "other")
PRIORITY_VALUES = ("high", "normal", "low")
STATUS_VALUES = ("open", "in_progress", "resolved", "rejected")

category_enum = postgresql.ENUM(*CATEGORY_VALUES, name="complaint_category", create_type=False)
priority_enum = postgresql.ENUM(*PRIORITY_VALUES, name="complaint_priority", create_type=False)
status_enum = postgresql.ENUM(*STATUS_VALUES, name="complaint_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "complaints",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=200), nullable=True),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("status", status_enum, server_default="open", nullable=False),
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=32), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_complaints")),
        sa.CheckConstraint("char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"),
        sa.CheckConstraint(
            "char_length(location) BETWEEN 3 AND 200", name="ck_complaints_location_length"
        ),
        sa.CheckConstraint(
            "triaged_by IN ('llm:groq', 'llm:ollama', 'rules', 'rules:fallback', 'simulated')",
            name="ck_complaints_triaged_by",
        ),
        sa.CheckConstraint("triage_latency_ms >= 0", name="ck_complaints_triage_latency_nonneg"),
    )
    # Dashboard list/stats: WHERE status = ? [AND priority = ?], GROUP BY status/priority.
    op.create_index("ix_complaints_status_priority", "complaints", ["status", "priority"])
    # Newest-first listing: ORDER BY created_at DESC.
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")
    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    priority_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)

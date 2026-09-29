import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.models.enums import Category, Priority, Status

_Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]
_Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
_Contact = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class ComplaintCreate(BaseModel):
    text: _Text
    location: _Location
    reporter_contact: _Contact | None = None

    @field_validator("reporter_contact")
    @classmethod
    def _blank_contact_is_none(cls, value: str | None) -> str | None:
        return value or None


class StatusUpdate(BaseModel):
    status: Status


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime


class ComplaintList(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int

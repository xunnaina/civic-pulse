"""The triage abstraction. Everything else depends on this, never on a concrete provider."""

from typing import Protocol

from pydantic import BaseModel, Field

from app.models.enums import Category, Priority


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult: ...

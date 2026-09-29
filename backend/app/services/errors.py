"""Domain errors raised by services. app/error_handlers.py maps them to HTTP responses."""

from app.models.enums import Status


class DomainError(Exception):
    """Base class for expected business-rule failures."""


class ComplaintNotFoundError(DomainError):
    def __init__(self, complaint_id: str) -> None:
        super().__init__(f"Complaint {complaint_id} not found")
        self.complaint_id = complaint_id


class InvalidTransitionError(DomainError):
    def __init__(self, current: Status, target: Status) -> None:
        super().__init__(f"Invalid status transition: {current.value} -> {target.value}")
        self.current = current
        self.target = target

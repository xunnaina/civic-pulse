"""Complaint status state machine, expressed as an explicit transition table."""

from collections.abc import Mapping
from typing import Final

from app.models.enums import Status
from app.services.errors import InvalidTransitionError

TRANSITIONS: Final[Mapping[Status, frozenset[Status]]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS, Status.REJECTED}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED, Status.REJECTED}),
    Status.RESOLVED: frozenset(),  # terminal
    Status.REJECTED: frozenset(),  # terminal
}


def assert_transition(current: Status, target: Status) -> None:
    """Raise InvalidTransitionError unless current -> target is in the table."""
    if target not in TRANSITIONS[current]:
        raise InvalidTransitionError(current, target)

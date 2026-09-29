import itertools

import pytest

from app.models.enums import Status
from app.services.errors import InvalidTransitionError
from app.services.state_machine import TRANSITIONS, assert_transition

ALLOWED = {
    (Status.OPEN, Status.IN_PROGRESS),
    (Status.OPEN, Status.REJECTED),
    (Status.IN_PROGRESS, Status.RESOLVED),
    (Status.IN_PROGRESS, Status.REJECTED),
}


@pytest.mark.parametrize(("current", "target"), sorted(ALLOWED))
def test_allowed_transitions_pass(current: Status, target: Status) -> None:
    assert_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [pair for pair in itertools.product(Status, Status) if pair not in ALLOWED],
)
def test_every_other_transition_is_rejected(current: Status, target: Status) -> None:
    with pytest.raises(InvalidTransitionError):
        assert_transition(current, target)


def test_error_message_names_the_attempted_transition() -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        assert_transition(Status.RESOLVED, Status.OPEN)
    assert str(exc_info.value) == "Invalid status transition: resolved -> open"


def test_terminal_states_have_no_outgoing_transitions() -> None:
    assert TRANSITIONS[Status.RESOLVED] == frozenset()
    assert TRANSITIONS[Status.REJECTED] == frozenset()

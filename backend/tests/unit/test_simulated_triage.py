import pytest

from app.providers.triage.simulated import SimulatedProviderError, SimulatedTriage

TEXT = "Burst water main flooding Street 12"


def test_failure_rate_one_always_fails() -> None:
    provider = SimulatedTriage(failure_rate=1.0)
    with pytest.raises(SimulatedProviderError):
        provider.triage(TEXT, "Street 12")


def test_failure_rate_zero_never_fails() -> None:
    provider = SimulatedTriage(failure_rate=0.0)
    assert all(provider.triage(TEXT, "Street 12").category for _ in range(50))


def _failure_pattern(seed: int) -> list[bool]:
    provider = SimulatedTriage(seed=seed, failure_rate=0.5)
    pattern = []
    for _ in range(30):
        try:
            provider.triage(TEXT, "Street 12")
            pattern.append(False)
        except SimulatedProviderError:
            pattern.append(True)
    return pattern


def test_same_seed_gives_same_failure_pattern() -> None:
    assert _failure_pattern(7) == _failure_pattern(7)

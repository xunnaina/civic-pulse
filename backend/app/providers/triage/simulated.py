"""Deterministic fake provider for CI: no network, seeded, configurable failure injection."""

import random
import threading

from app.providers.triage.base import TriageResult
from app.providers.triage.rules import classify


class SimulatedProviderError(RuntimeError):
    """Raised on purpose when failure injection triggers."""


class SimulatedTriage:
    name = "simulated"

    def __init__(self, *, seed: int = 0, failure_rate: float = 0.0) -> None:
        self._rng = random.Random(seed)
        self._failure_rate = failure_rate
        self._lock = threading.Lock()

    def triage(self, text: str, location: str) -> TriageResult:
        with self._lock:
            should_fail = self._rng.random() < self._failure_rate
        if should_fail:
            raise SimulatedProviderError("injected failure")
        result = classify(text)
        return TriageResult(
            category=result.category,
            priority=result.priority,
            summary=result.summary,
            confidence=result.confidence,
        )

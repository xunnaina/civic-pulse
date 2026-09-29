"""Triage orchestration: call the provider, fall back to rules on any failure, measure latency."""

import time
from dataclasses import dataclass

from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.rules import RuleBasedTriage

FALLBACK_TRIAGED_BY = "rules:fallback"


@dataclass(frozen=True, slots=True)
class TriageOutcome:
    result: TriageResult
    triaged_by: str
    latency_ms: int
    fallback_error: str | None = None  # exception class name when the fallback was used


class TriageService:
    def __init__(self, provider: TriageProvider, fallback: TriageProvider | None = None) -> None:
        self._provider = provider
        self._fallback: TriageProvider = fallback or RuleBasedTriage()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def triage(self, text: str, location: str) -> TriageOutcome:
        started = time.perf_counter()
        fallback_error: str | None = None
        try:
            result = self._provider.triage(text, location)
            triaged_by = self._provider.name
        except Exception as exc:  # any provider failure must degrade, never surface as a 500
            result = self._fallback.triage(text, location)
            triaged_by = FALLBACK_TRIAGED_BY
            fallback_error = type(exc).__name__
        latency_ms = round((time.perf_counter() - started) * 1000)
        return TriageOutcome(result, triaged_by, latency_ms, fallback_error)

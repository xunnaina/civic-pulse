from app.models.enums import Category, Priority
from app.providers.triage.base import TriageResult
from app.providers.triage.simulated import SimulatedTriage
from app.services.triage_service import TriageService


class AlwaysRaises:
    name = "llm:groq"

    def triage(self, text: str, location: str) -> TriageResult:
        raise TimeoutError("provider timed out")


class FixedResult:
    name = "llm:ollama"

    def triage(self, text: str, location: str) -> TriageResult:
        return TriageResult(
            category=Category.ROADS, priority=Priority.LOW, summary="fixed", confidence=0.5
        )


def test_successful_provider_result_is_used_and_attributed() -> None:
    outcome = TriageService(FixedResult()).triage("some complaint text", "Street 1")
    assert outcome.result.category == Category.ROADS
    assert outcome.triaged_by == "llm:ollama"
    assert outcome.fallback_error is None
    assert outcome.latency_ms >= 0


def test_provider_failure_falls_back_to_rules() -> None:
    outcome = TriageService(AlwaysRaises()).triage(
        "Burst water main flooding the street", "Street 1"
    )
    assert outcome.triaged_by == "rules:fallback"
    assert outcome.fallback_error == "TimeoutError"
    assert outcome.result.category == Category.WATER


def test_provider_name_is_exposed() -> None:
    assert TriageService(SimulatedTriage()).provider_name == "simulated"

"""Chooses the triage provider from settings (TRIAGE_PROVIDER)."""

from app.config import Settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


class ProviderUnavailableError(RuntimeError):
    """The configured provider is not implemented or cannot be built."""


def build_triage_provider(settings: Settings) -> TriageProvider:
    match settings.triage_provider:
        case "rules":
            return RuleBasedTriage()
        case "simulated":
            return SimulatedTriage(
                seed=settings.simulated_seed, failure_rate=settings.simulated_failure_rate
            )
        case other:
            raise ProviderUnavailableError(
                f"TRIAGE_PROVIDER={other!r} is not implemented yet; use 'rules' or 'simulated'"
            )

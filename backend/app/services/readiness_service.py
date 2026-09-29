"""Readiness: are all dependencies reachable? (Redis is added in Stage 3.)"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    checks: dict[str, bool]

    @property
    def ready(self) -> bool:
        return all(self.checks.values())

    @property
    def failed(self) -> list[str]:
        return [name for name, ok in self.checks.items() if not ok]


class ReadinessService:
    def __init__(self, checks: Mapping[str, Callable[[], None]]) -> None:
        self._checks = checks

    def check(self) -> ReadinessReport:
        results: dict[str, bool] = {}
        for name, check in self._checks.items():
            try:
                check()
                results[name] = True
            except Exception as exc:
                logger.warning(
                    "readiness check failed",
                    extra={"dependency": name, "error_class": type(exc).__name__},
                )
                results[name] = False
        return ReadinessReport(results)

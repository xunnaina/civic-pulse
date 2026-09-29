from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def ping(self) -> None:
        """Raises if PostgreSQL is unreachable."""
        self._session.execute(text("SELECT 1"))

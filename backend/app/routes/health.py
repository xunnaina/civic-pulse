from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.deps import get_readiness_service
from app.schemas.common import HealthOut, ReadyOut
from app.services.readiness_service import ReadinessService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    """Liveness: the process is alive. Deliberately touches no dependency."""
    return HealthOut(status="ok")


@router.get(
    "/ready",
    responses={200: {"model": ReadyOut}, 503: {"model": ReadyOut}},
)
def ready(service: Annotated[ReadinessService, Depends(get_readiness_service)]) -> JSONResponse:
    """Readiness: 200 only if every dependency is reachable, else 503 naming the failed ones."""
    report = service.check()
    body = ReadyOut(
        status="ready" if report.ready else "not_ready",
        checks={name: "ok" if ok else "fail" for name, ok in report.checks.items()},
        failed=report.failed,
    )
    return JSONResponse(status_code=200 if report.ready else 503, content=body.model_dump())

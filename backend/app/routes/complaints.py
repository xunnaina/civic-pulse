"""HTTP layer only: parse input, call a service, return the response."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import get_complaint_service
from app.models.complaint import Complaint
from app.models.enums import Category, Priority, Status
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.schemas.complaint import ComplaintCreate, ComplaintList, ComplaintOut, StatusUpdate
from app.services.complaint_service import ComplaintService
from app.services.errors import ComplaintNotFoundError

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

ServiceDep = Annotated[ComplaintService, Depends(get_complaint_service)]


def complaint_id_param(complaint_id: str) -> uuid.UUID:
    """A malformed id can never match a complaint, so it is a 404 rather than a validation error."""
    try:
        return uuid.UUID(complaint_id)
    except ValueError:
        raise ComplaintNotFoundError(complaint_id) from None


ComplaintIdDep = Annotated[uuid.UUID, Depends(complaint_id_param)]


@router.post(
    "",
    response_model=ComplaintOut,
    status_code=201,
    responses={400: {"model": ValidationErrorResponse}},
)
def create_complaint(payload: ComplaintCreate, service: ServiceDep) -> Complaint:
    return service.create(
        text=payload.text, location=payload.location, reporter_contact=payload.reporter_contact
    )


@router.get(
    "",
    response_model=ComplaintList,
    responses={400: {"model": ValidationErrorResponse}},
)
def list_complaints(
    service: ServiceDep,
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ComplaintList:
    items, total = service.list_complaints(
        category=category, priority=priority, status=status, page=page, page_size=page_size
    )
    return ComplaintList(
        items=[ComplaintOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintOut,
    responses={404: {"model": ErrorResponse}},
)
def get_complaint(complaint_id: ComplaintIdDep, service: ServiceDep) -> Complaint:
    return service.get(complaint_id)


@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintOut,
    responses={
        400: {"model": ValidationErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def update_status(
    complaint_id: ComplaintIdDep, payload: StatusUpdate, service: ServiceDep
) -> Complaint:
    return service.change_status(complaint_id, payload.status)

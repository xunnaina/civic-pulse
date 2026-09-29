"""Maps validation and domain errors to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.errors import ComplaintNotFoundError, InvalidTransitionError


def _field_name(loc: tuple[int | str, ...], error_type: str) -> str:
    if error_type == "json_invalid":
        return "body"
    return ".".join(str(part) for part in loc[1:]) or str(loc[0])


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"field": _field_name(tuple(err["loc"]), err["type"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "Validation failed", "errors": errors})


async def _not_found(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ComplaintNotFoundError)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def _invalid_transition(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, InvalidTransitionError)
    return JSONResponse(status_code=409, content={"detail": str(exc)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(ComplaintNotFoundError, _not_found)
    app.add_exception_handler(InvalidTransitionError, _invalid_transition)

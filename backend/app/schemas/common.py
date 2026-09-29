from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    detail: str
    errors: list[FieldError]


class HealthOut(BaseModel):
    status: str


class ReadyOut(BaseModel):
    status: str
    checks: dict[str, str]
    failed: list[str]

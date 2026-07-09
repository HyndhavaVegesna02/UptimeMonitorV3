"""Centralized domain exception to HTTP response mapping registry.

Cites: Proposal (2026-07-10) §3.4 G2, §6.2.
ONE registry: a dict of exception type -> HTTP status, installed as FastAPI
exception handlers via a single handler factory. Every response body stays
`{"detail": str(exc)}`.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1._shared.validation import SyntacticValidationError
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.topology import (
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)
from src.core.services.approval import (
    ProposalNotFoundError,
    ProposalNotOpenError,
)

_STATUS_BY_EXCEPTION: dict[type[Exception], int] = {
    SyntacticValidationError: 422,
    SignalNotFoundError: 404,
    ComponentNotFoundError: 404,
    ProposalNotFoundError: 404,
    SignalIntervalUnconfiguredError: 409,
    ProposalNotOpenError: 409,
}


def _make_handler(status_code: int):
    """Build a FastAPI exception handler closing over a fixed HTTP status code."""

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


def install_error_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application instance.

    Cites: Proposal (2026-07-10) §6.2.
    """
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exc_type, _make_handler(status_code))

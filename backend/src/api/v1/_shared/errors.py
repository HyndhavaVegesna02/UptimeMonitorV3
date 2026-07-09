"""Centralized domain exception to HTTP response mapping registry.

Cites: Proposal (2026-07-10) §3.4 G2, §6.2.
Provides ONE registry to map domain/syntactic exceptions to their corresponding
HTTP status codes and {"detail": ...} response bodies at the API edge.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.domain.component import ComponentNotFoundError
from src.core.domain.topology import (
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)
from src.core.services.approval import (
    ProposalNotFoundError,
    ProposalNotOpenError,
)


def install_error_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application instance.

    Cites: Proposal (2026-07-10) §6.2.
    """

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(SignalNotFoundError)
    async def signal_not_found_handler(
        request: Request, exc: SignalNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ComponentNotFoundError)
    async def component_not_found_handler(
        request: Request, exc: ComponentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ProposalNotFoundError)
    async def proposal_not_found_handler(
        request: Request, exc: ProposalNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(SignalIntervalUnconfiguredError)
    async def signal_interval_unconfigured_handler(
        request: Request, exc: SignalIntervalUnconfiguredError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProposalNotOpenError)
    async def proposal_not_open_handler(
        request: Request, exc: ProposalNotOpenError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

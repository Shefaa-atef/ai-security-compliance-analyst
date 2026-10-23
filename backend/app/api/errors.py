"""Error handlers that return safe JSON bodies with a request id.

Responses never echo the submitted scenario, provider error text or stack traces.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unhandled_error)


def error_response(request: Request, status: int, detail: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status,
        content={"detail": detail, "request_id": request_id},
        headers={"X-Request-ID": request_id or ""},
    )


async def _validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
    # The default handler echoes the submitted input back, and the scenario may be sensitive.
    return error_response(request, 422, "Scenario must be between 20 and 12,000 characters after trimming.")


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error_response(request, exc.status_code, str(exc.detail))


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    log.error(
        "Unhandled error request_id=%s type=%s",
        getattr(request.state, "request_id", None),
        type(exc).__name__,
    )
    return error_response(request, 500, "The assessment could not be completed.")

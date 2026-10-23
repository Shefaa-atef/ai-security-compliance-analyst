"""FastAPI entry point for the AI Security & Compliance Analyst backend."""
import logging
import uuid

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import service
from .agent import AssessmentAgent, AssessmentUnavailable
from .config import get_settings
from .rate_limit import RateLimiter
from .schemas import AssessmentRequest, AssessmentResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

settings = get_settings()
limiter = RateLimiter(settings.rate_limit_per_minute)

app = FastAPI(title="AI Security & Compliance Analyst API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def _error(request: Request, status: int, detail: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(status_code=status, content={"detail": detail, "request_id": request_id},
                        headers={"X-Request-ID": request_id or ""})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
    # The default handler echoes the submitted input back; the scenario may be sensitive.
    return _error(request, 422, "Scenario must be between 20 and 12,000 characters after trimming.")


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error(request, exc.status_code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    # Never return stack traces or provider error text to the browser.
    log.error("Unhandled error request_id=%s type=%s", getattr(request.state, "request_id", None),
              type(exc).__name__)
    return _error(request, 500, "The assessment could not be completed.")


def get_agent() -> AssessmentAgent:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AI assessment service is not configured.")
    # Retries are handled by the agent's overall deadline, not by stacking SDK retries.
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, max_retries=0)
    return AssessmentAgent(client, settings.anthropic_model, settings.max_agent_turns,
                           deadline_seconds=settings.request_deadline_seconds)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ai_configured": bool(settings.anthropic_api_key)}


@app.post("/api/assess", response_model=AssessmentResponse)
def assess(body: AssessmentRequest, request: Request, agent: AssessmentAgent = Depends(get_agent)):
    client_key = request.client.host if request.client else "unknown"
    if not limiter.allow(client_key):
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")
    try:
        return service.assess(body.scenario, agent, settings.audit_log_path,
                              request_id=request.state.request_id)
    except service.ScenarioRejected:
        raise HTTPException(status_code=422, detail="Scenario must contain at least 20 meaningful characters.")
    except AssessmentUnavailable:
        raise HTTPException(status_code=503, detail="The AI assessment service is unavailable.")

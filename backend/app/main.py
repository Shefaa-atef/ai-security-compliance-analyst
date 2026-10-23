"""FastAPI entry point for the AI Security & Compliance Analyst backend."""
import logging

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
)


def get_agent() -> AssessmentAgent:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AI assessment service is not configured.")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=55.0, max_retries=1)
    return AssessmentAgent(client, settings.anthropic_model, settings.max_agent_turns)


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
    # Never return stack traces or provider error text to the browser.
    log.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "The assessment could not be completed."})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ai_configured": bool(settings.anthropic_api_key), "model": settings.anthropic_model}


@app.post("/api/assess", response_model=AssessmentResponse)
def assess(body: AssessmentRequest, request: Request, agent: AssessmentAgent = Depends(get_agent)):
    client_key = request.client.host if request.client else "unknown"
    if not limiter.allow(client_key):
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")
    try:
        return service.assess(body.scenario, agent, settings.audit_log_path)
    except service.ScenarioRejected:
        raise HTTPException(status_code=422, detail="Scenario must contain at least 20 meaningful characters.")
    except AssessmentUnavailable:
        raise HTTPException(status_code=503, detail="The AI assessment service is unavailable.")

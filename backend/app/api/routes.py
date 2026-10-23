"""HTTP endpoints."""

from fastapi import APIRouter, HTTPException, Request

from .. import pipeline
from ..agent import AssessmentUnavailable
from ..schemas import AssessmentRequest, AssessmentResponse
from .dependencies import AgentDep, LimiterDep, SettingsDep

router = APIRouter(prefix="/api")


@router.get("/health")
def health(settings: SettingsDep) -> dict:
    return {"status": "ok", "ai_configured": bool(settings.anthropic_api_key)}


@router.post("/assess", response_model=AssessmentResponse)
def assess(
    body: AssessmentRequest,
    request: Request,
    settings: SettingsDep,
    limiter: LimiterDep,
    agent: AgentDep,
) -> AssessmentResponse:
    client_address = request.client.host if request.client else "unknown"
    if not limiter.allow(client_address):
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")

    try:
        return pipeline.assess(body.scenario, agent, settings.audit_log_path, request.state.request_id)
    except pipeline.ScenarioRejected:
        raise HTTPException(
            status_code=422, detail="Scenario must contain at least 20 meaningful characters."
        ) from None
    except AssessmentUnavailable:
        raise HTTPException(status_code=503, detail="The AI assessment service is unavailable.") from None

"""Objects the routes depend on. Tests replace them through FastAPI dependency overrides."""

from functools import lru_cache
from typing import Annotated

import anthropic
from fastapi import Depends, HTTPException

from ..agent import AssessmentAgent
from ..config import Settings, get_settings
from ..rate_limit import RateLimiter

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_limiter() -> RateLimiter:
    return RateLimiter(get_settings().rate_limit_per_minute)


@lru_cache
def _claude_client(api_key: str) -> anthropic.Anthropic:
    # One client per key, reused across requests so HTTP connections are pooled.
    # Retries are left to the agent's overall time budget rather than stacked SDK retries.
    return anthropic.Anthropic(api_key=api_key, max_retries=0)


def get_agent(settings: SettingsDep) -> AssessmentAgent:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="AI assessment service is not configured.")
    return AssessmentAgent(
        _claude_client(settings.anthropic_api_key),
        settings.anthropic_model,
        max_turns=settings.max_agent_turns,
        deadline_seconds=settings.request_deadline_seconds,
    )


AgentDep = Annotated[AssessmentAgent, Depends(get_agent)]
LimiterDep = Annotated[RateLimiter, Depends(get_limiter)]

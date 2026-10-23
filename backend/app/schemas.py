"""Request and response models.

`AgentAssessment` is what the model must return (kept simple so it is a valid
structured-output schema). `AssessmentResponse` is what the API returns after
guardrails run; it matches the contract in frontend/src/lib/api.js.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["supported", "gap", "needs_clarification", "not_applicable"]
RiskLevel = Literal["low", "medium", "high", "unknown"]

MIN_SCENARIO_CHARS = 20
MAX_SCENARIO_CHARS = 12_000


class AssessmentRequest(BaseModel):
    scenario: str = Field(min_length=MIN_SCENARIO_CHARS, max_length=MAX_SCENARIO_CHARS)

    @field_validator("scenario", mode="before")
    @classmethod
    def _trim(cls, value):
        # Length limits apply to the trimmed text, matching the frontend.
        return value.strip() if isinstance(value, str) else value


class Finding(BaseModel):
    requirement_id: str
    status: Status
    evidence: list[str] = Field(
        description=(
            "Verbatim quotes copied from the scenario. "
            "Empty if nothing in the scenario addresses the requirement."
        )
    )
    explanation: str
    recommendation: str


class AgentAssessment(BaseModel):
    summary: str
    risk_level: RiskLevel
    risk_rationale: str
    findings: list[Finding]
    next_actions: list[str]
    follow_up_questions: list[str]


class AssessmentResponse(AgentAssessment):
    assessment_id: str
    review_steps: list[str]
    guardrail_notes: list[str] = []
    model: str

"""Assessment pipeline: input guardrails, agent, output guardrails, audit log."""

import time
import uuid
from collections import Counter

from . import audit, review_trail
from .agent import AssessmentRunner, AssessmentUnavailable
from .governance import risk_signals
from .guardrails import output as output_guardrails
from .guardrails.input import prepare_input
from .i18n import ResponseLanguage
from .schemas import MIN_SCENARIO_CHARS, AssessmentResponse


class ScenarioRejected(ValueError):
    """The scenario is unusable after input guardrails (for example, only invisible characters)."""


def assess(
    scenario: str,
    agent: AssessmentRunner,
    audit_path: str,
    request_id: str | None = None,
    response_language: ResponseLanguage = "en",
) -> AssessmentResponse:
    started = time.monotonic()
    prepared = prepare_input(scenario)
    event = {
        "request_id": request_id,
        "response_language": response_language,
        "assessment_id": str(uuid.uuid4()),
        "scenario_sha256": audit.scenario_hash(prepared.text),
        "scenario_chars": len(prepared.text),
        "redactions": prepared.redactions,
        "injection_flagged": bool(prepared.injection_signals),
    }

    def elapsed_ms() -> int:
        return round((time.monotonic() - started) * 1000)

    if len(prepared.text) < MIN_SCENARIO_CHARS:
        audit.write(audit_path, {**event, "outcome": "rejected_input"})
        raise ScenarioRejected("Scenario is too short after cleanup")

    try:
        run = agent.run(prepared.text, response_language=response_language)
    except AssessmentUnavailable as exc:
        audit.write(
            audit_path,
            {**event, "outcome": "ai_unavailable", "reason": str(exc), "duration_ms": elapsed_ms()},
        )
        raise

    signals = risk_signals.scan(prepared.text)
    guarded = output_guardrails.apply(run.assessment, prepared.text, signals, response_language)
    response = AssessmentResponse(
        **guarded.assessment.model_dump(),
        assessment_id=event["assessment_id"],
        review_steps=review_trail.build(
            prepared, run.tool_calls, run.model, guarded.corrections, response_language
        ),
        guardrail_notes=prepared.localized_notes(response_language) + guarded.corrections.notes,
        model=run.model,
        response_language=response_language,
    )

    audit.write(
        audit_path,
        {
            **event,
            "outcome": "completed",
            "duration_ms": elapsed_ms(),
            "model": run.model,
            "tool_calls": [call["tool"] for call in run.tool_calls],
            "risk_signals": list(signals),
            "risk_level": response.risk_level,
            "status_counts": dict(Counter(finding.status for finding in response.findings)),
            "guardrail_notes": response.guardrail_notes,
        },
    )
    return response

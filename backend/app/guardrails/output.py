"""Guardrails applied to the model's assessment before it is returned.

The model's output is never trusted as-is. Evidence checks make the report
traceable, and policy rules stop the model from rating a use case more
leniently than policy allows. Every correction is reported back to the user.
"""

from dataclasses import dataclass

from ..schemas import AgentAssessment
from . import evidence, policy
from .corrections import Corrections

MAX_LIST_ITEMS = 5


@dataclass
class GuardrailResult:
    assessment: AgentAssessment
    corrections: Corrections


def apply(assessment: AgentAssessment, scenario: str, signals: dict) -> GuardrailResult:
    corrections = Corrections()

    findings = evidence.complete_findings(assessment.findings, corrections)
    for finding in findings:
        finding.explanation = _text_or(finding.explanation, "No explanation was provided.")
        finding.recommendation = _text_or(finding.recommendation, "Review this requirement manually.")
    evidence.verify_quotes(findings, scenario, corrections)
    evidence.require_evidence_for_support(findings, corrections)

    by_id = {finding.requirement_id: finding for finding in findings}
    policy.enforce_human_oversight(by_id, signals, corrections)
    policy.enforce_third_party_review(by_id, signals, corrections)
    policy.enforce_missing_control_uncertainty(by_id, corrections)
    risk_level, risk_rationale = policy.apply_risk_floor(
        assessment.risk_level,
        _text_or(assessment.risk_rationale, "No rationale was provided."),
        signals,
        corrections,
    )
    policy.enforce_high_risk_review(by_id, risk_level, corrections)

    cleaned = AgentAssessment(
        summary=_text_or(assessment.summary, "Assessment completed. Review the findings below."),
        risk_level=risk_level,
        risk_rationale=risk_rationale,
        findings=findings,
        next_actions=_clean_list(assessment.next_actions),
        follow_up_questions=_clean_list(assessment.follow_up_questions),
    )
    return GuardrailResult(assessment=cleaned, corrections=corrections)


def _text_or(value: str, fallback: str) -> str:
    return value.strip() if value and value.strip() else fallback


def _clean_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()][:MAX_LIST_ITEMS]

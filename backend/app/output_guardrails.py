"""Guardrails applied to the model's assessment before it is returned.

The model's output is never trusted as-is. These deterministic checks make
the report traceable (every quote really comes from the scenario) and stop
the model from rating a use case more leniently than policy allows. Each
correction is reported back to the user as a guardrail note.
"""
import re
from dataclasses import dataclass, field

from . import risk_signals
from .requirements_catalog import REQUIREMENT_IDS
from .schemas import AgentAssessment, Finding

MAX_QUOTES = 3
MAX_QUOTE_CHARS = 300


@dataclass
class GuardrailResult:
    assessment: AgentAssessment
    notes: list[str] = field(default_factory=list)
    quotes_verified: int = 0
    quotes_removed: int = 0
    status_changes: int = 0


def _normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def _clean_quote(quote: str) -> str:
    return quote.strip().strip('"\'').strip().rstrip(".,;:").strip()


def _text_or(value: str, fallback: str) -> str:
    return value.strip() if value and value.strip() else fallback


def apply(assessment: AgentAssessment, scenario: str, signals: dict) -> GuardrailResult:
    result = GuardrailResult(assessment=assessment)
    notes = result.notes
    source = _normalize(scenario)

    # 1. Exactly one finding per catalog requirement, in catalog order.
    by_id: dict[str, Finding] = {}
    for finding in assessment.findings:
        if finding.requirement_id in REQUIREMENT_IDS and finding.requirement_id not in by_id:
            by_id[finding.requirement_id] = finding
    missing = [rid for rid in REQUIREMENT_IDS if rid not in by_id]
    for rid in missing:
        by_id[rid] = Finding(
            requirement_id=rid, status="needs_clarification", evidence=[],
            explanation="The AI assessment did not cover this requirement.",
            recommendation="Assess this requirement manually.",
        )
    if missing:
        notes.append(f"The AI did not assess {', '.join(missing)}; marked for manual review.")

    findings: list[Finding] = []
    for rid in REQUIREMENT_IDS:
        f = by_id[rid].model_copy(deep=True)
        f.explanation = _text_or(f.explanation, "No explanation was provided.")
        f.recommendation = _text_or(f.recommendation, "Review this requirement manually.")

        # 2. Keep only quotes that appear verbatim in the scenario.
        verified = []
        for quote in f.evidence:
            cleaned = _clean_quote(quote)[:MAX_QUOTE_CHARS]
            if cleaned and _normalize(cleaned) in source and cleaned not in verified:
                verified.append(cleaned)
            else:
                result.quotes_removed += 1
        f.evidence = verified[:MAX_QUOTES]
        result.quotes_verified += len(f.evidence)

        # 3. A control cannot be "supported" without verified evidence.
        if f.status == "supported" and not f.evidence:
            _change(result, f, "needs_clarification",
                    f"{rid} was rated supported without evidence from the scenario; changed to needs clarification.")
        findings.append(f)

    by_id = {f.requirement_id: f for f in findings}

    # 4. Policy rules the model may not relax.
    automated = "automated_decision" in signals and "human_review" not in signals
    oversight = by_id["AI-003"]
    if automated and oversight.status != "gap":
        _change(result, oversight, "gap",
                "AI-003 changed to gap: the AI output drives decisions and no human review is described.")
        oversight.recommendation = "Require a qualified person to review and approve every AI recommendation before a decision is made."

    third_party = by_id["AI-006"]
    if "third_party" in signals and third_party.status == "not_applicable":
        _change(result, third_party, "needs_clarification",
                "AI-006 changed to needs clarification: the scenario uses a third-party service.")

    # 5. Risk level cannot fall below the policy floor.
    risk_level = assessment.risk_level
    risk_rationale = _text_or(assessment.risk_rationale, "No rationale was provided.")
    floor, reason = risk_signals.risk_floor(signals)
    if not risk_signals.at_least(risk_level, floor):
        notes.append(f"Risk level raised from {risk_level} to {floor}. {reason}")
        risk_rationale = f"{risk_rationale} Policy minimum applied: {reason}"
        risk_level = floor

    high_risk_review = by_id["AI-008"]
    if risk_level == "high" and high_risk_review.status in ("supported", "not_applicable") and not high_risk_review.evidence:
        _change(result, high_risk_review, "needs_clarification",
                "AI-008 changed to needs clarification: the use case is high risk and no completed review is described.")

    result.assessment = AgentAssessment(
        summary=_text_or(assessment.summary, "Assessment completed. Review the findings below."),
        risk_level=risk_level,
        risk_rationale=risk_rationale,
        findings=findings,
        next_actions=[a.strip() for a in assessment.next_actions if a and a.strip()][:5],
        follow_up_questions=[q.strip() for q in assessment.follow_up_questions if q and q.strip()][:5],
    )
    if result.quotes_removed:
        notes.append(f"{result.quotes_removed} evidence quote(s) were removed because they do not appear in the scenario.")
    return result


def _change(result: GuardrailResult, finding: Finding, status: str, note: str) -> None:
    finding.status = status
    result.status_changes += 1
    result.notes.append(note)

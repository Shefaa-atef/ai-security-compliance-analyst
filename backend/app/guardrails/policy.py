"""Policy rules the model is not allowed to relax.

Each rule looks at the deterministic risk signals, not at the model's opinion,
and can only make the assessment stricter.
"""
from ..governance import risk_signals
from ..schemas import Finding, RiskLevel
from .corrections import Corrections


def enforce_human_oversight(findings: dict[str, Finding], signals: dict, corrections: Corrections) -> None:
    """AI-003: automated decisions without described human review are always a gap."""
    automated = "automated_decision" in signals and "human_review" not in signals
    oversight = findings["AI-003"]
    if automated and oversight.status != "gap":
        corrections.change_status(
            oversight, "gap",
            "AI-003 changed to gap: the AI output drives decisions and no human review is described.",
        )
        oversight.recommendation = (
            "Require a qualified person to review and approve every AI recommendation before a decision is made."
        )


def enforce_third_party_review(findings: dict[str, Finding], signals: dict, corrections: Corrections) -> None:
    """AI-006: a detected third-party service makes the vendor assessment applicable."""
    third_party = findings["AI-006"]
    if "third_party" in signals and third_party.status == "not_applicable":
        corrections.change_status(
            third_party, "needs_clarification",
            "AI-006 changed to needs clarification: the scenario uses a third-party service.",
        )


def apply_risk_floor(
    level: RiskLevel, rationale: str, signals: dict, corrections: Corrections
) -> tuple[RiskLevel, str]:
    """Raise the risk level to the policy minimum. Never lowers it."""
    floor, reason = risk_signals.risk_floor(signals)
    if risk_signals.at_least(level, floor):
        return level, rationale
    corrections.add_note(f"Risk level raised from {level} to {floor}. {reason}")
    return floor, f"{rationale} Policy minimum applied: {reason}"


def enforce_high_risk_review(findings: dict[str, Finding], level: RiskLevel, corrections: Corrections) -> None:
    """AI-008: a high-risk use case needs evidence of an additional review."""
    review = findings["AI-008"]
    if level == "high" and review.status in ("supported", "not_applicable") and not review.evidence:
        corrections.change_status(
            review, "needs_clarification",
            "AI-008 changed to needs clarification: the use case is high risk and no completed review "
            "is described.",
        )

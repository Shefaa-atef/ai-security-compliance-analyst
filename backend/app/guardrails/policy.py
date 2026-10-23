"""Policy rules the model is not allowed to relax.

Each rule looks at the deterministic risk signals, not at the model's opinion,
and can only make the assessment stricter.
"""

import re

from ..governance import risk_signals
from ..schemas import Finding, RiskLevel
from .corrections import Corrections


def enforce_human_oversight(findings: dict[str, Finding], signals: dict, corrections: Corrections) -> None:
    """AI-003: automated decisions without described human review are always a gap."""
    automated = "automated_decision" in signals and "human_review" not in signals
    oversight = findings["AI-003"]
    if automated and oversight.status != "gap":
        corrections.change_status(
            oversight,
            "gap",
            "AI-003 changed to gap: the AI output drives decisions and no human review is described.",
        )
        oversight.recommendation = (
            "Require a qualified person to review and approve every AI recommendation "
            "before a decision is made."
        )


def enforce_third_party_review(findings: dict[str, Finding], signals: dict, corrections: Corrections) -> None:
    """AI-006: a detected third-party service makes the vendor assessment applicable."""
    third_party = findings["AI-006"]
    if "third_party" in signals and third_party.status == "not_applicable":
        corrections.change_status(
            third_party,
            "needs_clarification",
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


def enforce_high_risk_review(
    findings: dict[str, Finding], level: RiskLevel, corrections: Corrections
) -> None:
    """AI-008: a high-risk use case needs evidence of an additional review."""
    review = findings["AI-008"]
    if level == "high" and (
        review.status == "not_applicable" or (review.status == "supported" and not review.evidence)
    ):
        corrections.change_status(
            review,
            "needs_clarification",
            "AI-008 changed to needs clarification: high-risk use cases require an additional review. "
            "The finding does not establish that an applicable review has been completed.",
        )


_EXPLICIT_GAP = {
    "AI-002": re.compile(
        r"\b(?:without|no|not|lack\w*)\b[^.!?]{0,60}"
        r"\b(?:controls?|protect\w*|encrypt\w*|redact\w*|consent|safeguards?)\b"
        r"|\b(?:unencrypted|unprotected|unredacted|publicly accessible)\b",
        re.I,
    ),
    "AI-006": re.compile(
        r"\b(?:without|no|not|lack\w*|skip\w*|bypass\w*)\b[^.!?]{0,60}"
        r"\b(?:assess\w*|review\w*|vet\w*|approv\w*)\b"
        r"|\b(?:assess\w*|review\w*)\b[^.!?]{0,20}\b(?:not|never|skipped|bypassed)\b",
        re.I,
    ),
}


def enforce_missing_control_uncertainty(findings: dict[str, Finding], corrections: Corrections) -> None:
    """Sensitive processing or vendor use alone does not prove a control violation."""
    for requirement_id, pattern in _EXPLICIT_GAP.items():
        finding = findings[requirement_id]
        if finding.status == "gap" and not any(pattern.search(quote) for quote in finding.evidence):
            corrections.change_status(
                finding,
                "needs_clarification",
                f"{requirement_id}: the cited evidence does not explicitly establish a control failure. "
                "Confirm the controls rather than treating an omitted description as a violation.",
            )

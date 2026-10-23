"""Acme Financial Services AI governance requirements.

This is the internal knowledge base the agent retrieves from through tools.
`guidance` tells the model what evidence satisfies each control and which
signals usually indicate a gap, so conclusions are grounded in policy text
rather than the model's general knowledge.
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Requirement:
    id: str
    title: str
    description: str
    satisfied_when: str
    gap_signals: str

    def to_dict(self) -> dict:
        return asdict(self)


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        "AI-001", "Business ownership",
        "AI applications must have an identified business owner.",
        "A named accountable person or role owns the application, its risks and its approval.",
        "Only a team or department is mentioned; no accountable owner is named.",
    ),
    Requirement(
        "AI-002", "Sensitive information",
        "Sensitive or confidential information must not be submitted to an AI system without appropriate controls.",
        "Data classification, minimization, redaction or masking, retention limits and provider data-handling terms are described.",
        "Personal, customer, financial, HR, credential or security data is processed and controls are not described.",
    ),
    Requirement(
        "AI-003", "Human oversight",
        "AI-generated outputs used for business decisions must have appropriate human oversight.",
        "A qualified person reviews and can override every output before it affects a business decision or a person.",
        "Outputs are applied automatically, are the primary input to a decision, or review is not described.",
    ),
    Requirement(
        "AI-004", "Logging & monitoring",
        "AI applications must maintain appropriate logging and monitoring.",
        "Prompts, outputs, user actions and errors are logged with retention and redaction rules, and someone monitors them.",
        "Logging, audit trails or monitoring responsibilities are not described.",
    ),
    Requirement(
        "AI-005", "Access controls",
        "AI applications must have defined access controls.",
        "Authentication, role-based or least-privilege authorization and access to connected data sources are defined.",
        "Who may use the system, or what data the system itself can reach, is not defined.",
    ),
    Requirement(
        "AI-006", "Third-party assessment",
        "Third-party AI models and services must undergo appropriate security assessment.",
        "Any external model, API or data source has a completed security and contractual assessment. Not applicable when no third party is involved.",
        "A third-party hosted model, API or external data feed is used and no assessment is mentioned.",
    ),
    Requirement(
        "AI-007", "Intended use & limitations",
        "AI applications must have documented intended use and limitations.",
        "Allowed uses, prohibited uses, known limitations and failure modes are documented.",
        "Only the goal is described; limitations, prohibited uses or accuracy expectations are missing.",
    ),
    Requirement(
        "AI-008", "High-risk review",
        "High-risk AI use cases must undergo additional review before deployment.",
        "The use case has been risk-classified and, if high risk, an additional governance review is completed or scheduled.",
        "The use case affects people's employment, finances or rights, or processes sensitive data at scale, and no additional review is mentioned.",
    ),
)

REQUIREMENT_IDS: tuple[str, ...] = tuple(r.id for r in REQUIREMENTS)
_BY_ID = {r.id: r for r in REQUIREMENTS}


def list_requirements() -> list[dict]:
    """Short catalog view: id, title and requirement text."""
    return [{"id": r.id, "title": r.title, "description": r.description} for r in REQUIREMENTS]


def get_guidance(ids: list[str]) -> list[dict]:
    """Full guidance for the requested ids. Unknown ids are reported, not invented."""
    return [_BY_ID[i].to_dict() if i in _BY_ID else {"id": i, "error": "unknown requirement id"} for i in ids]

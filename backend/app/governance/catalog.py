"""Acme Financial Services AI governance requirements.

This is the internal knowledge base the agent retrieves through tools. Each
requirement carries guidance on what evidence satisfies it and which signals
usually indicate a gap, so conclusions are grounded in policy text rather than
the model's general knowledge.
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
        id="AI-001",
        title="Business ownership",
        description="AI applications must have an identified business owner.",
        satisfied_when="A named accountable person or role owns the application, its risks and its approval.",
        gap_signals="Only a team or department is mentioned; no accountable owner is named.",
    ),
    Requirement(
        id="AI-002",
        title="Sensitive information",
        description=(
            "Sensitive or confidential information must not be submitted to an AI system "
            "without appropriate controls."
        ),
        satisfied_when=(
            "Data classification, minimization, redaction or masking, retention limits and "
            "provider data-handling terms are described."
        ),
        gap_signals=(
            "Personal, customer, financial, HR, credential or security data is processed and "
            "controls are not described."
        ),
    ),
    Requirement(
        id="AI-003",
        title="Human oversight",
        description="AI-generated outputs used for business decisions must have appropriate human oversight.",
        satisfied_when=(
            "A qualified person reviews and can override every output before it affects a "
            "business decision or a person."
        ),
        gap_signals=(
            "Outputs are applied automatically, are the primary input to a decision, or review "
            "is not described."
        ),
    ),
    Requirement(
        id="AI-004",
        title="Logging & monitoring",
        description="AI applications must maintain appropriate logging and monitoring.",
        satisfied_when=(
            "Prompts, outputs, user actions and errors are logged with retention and redaction "
            "rules, and someone monitors them."
        ),
        gap_signals="Logging, audit trails or monitoring responsibilities are not described.",
    ),
    Requirement(
        id="AI-005",
        title="Access controls",
        description="AI applications must have defined access controls.",
        satisfied_when=(
            "Authentication, role-based or least-privilege authorization and access to connected "
            "data sources are defined."
        ),
        gap_signals="Who may use the system, or what data the system itself can reach, is not defined.",
    ),
    Requirement(
        id="AI-006",
        title="Third-party assessment",
        description="Third-party AI models and services must undergo appropriate security assessment.",
        satisfied_when=(
            "Any external model, API or data source has a completed security and contractual "
            "assessment. Not applicable when no third party is involved."
        ),
        gap_signals=(
            "A third-party hosted model, API or external data feed is used and no assessment is mentioned."
        ),
    ),
    Requirement(
        id="AI-007",
        title="Intended use & limitations",
        description="AI applications must have documented intended use and limitations.",
        satisfied_when="Allowed uses, prohibited uses, known limitations and failure modes are documented.",
        gap_signals=(
            "Only the goal is described; limitations, prohibited uses or accuracy expectations are missing."
        ),
    ),
    Requirement(
        id="AI-008",
        title="High-risk review",
        description="High-risk AI use cases must undergo additional review before deployment.",
        satisfied_when=(
            "The use case has been risk-classified and, if high risk, an additional governance "
            "review is completed or scheduled."
        ),
        gap_signals=(
            "The use case affects people's employment, finances or rights, or processes sensitive "
            "data at scale, and no additional review is mentioned."
        ),
    ),
)

REQUIREMENT_IDS: tuple[str, ...] = tuple(requirement.id for requirement in REQUIREMENTS)
_BY_ID = {requirement.id: requirement for requirement in REQUIREMENTS}


def list_requirements() -> list[dict]:
    """Short catalog view: id, title and requirement text."""
    return [{"id": r.id, "title": r.title, "description": r.description} for r in REQUIREMENTS]


def get_guidance(ids: list[str]) -> list[dict]:
    """Full guidance for the requested ids. Unknown ids are reported, not invented."""
    return [
        _BY_ID[rid].to_dict() if rid in _BY_ID else {"id": rid, "error": "unknown requirement id"}
        for rid in ids
    ]

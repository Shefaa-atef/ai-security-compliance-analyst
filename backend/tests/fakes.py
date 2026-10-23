"""A scripted stand-in for the Anthropic client so the workflow can be tested offline."""

from types import SimpleNamespace

from app.governance.catalog import REQUIREMENT_IDS
from app.schemas import AgentAssessment, Finding


def tool_use(name: str, tool_id: str, args: dict | None = None):
    return SimpleNamespace(type="tool_use", name=name, id=tool_id, input=args or {})


def tool_turn(*blocks):
    return SimpleNamespace(
        stop_reason="tool_use", content=list(blocks), parsed_output=None, model="fake-model"
    )


def final_turn(assessment: AgentAssessment):
    return SimpleNamespace(stop_reason="end_turn", content=[], parsed_output=assessment, model="fake-model")


def make_assessment(**overrides) -> AgentAssessment:
    findings = [
        Finding(
            requirement_id=rid,
            status="needs_clarification",
            evidence=[],
            explanation="Not described.",
            recommendation="Document this control.",
        )
        for rid in REQUIREMENT_IDS
    ]
    data = dict(
        summary="Initial assessment.",
        risk_level="medium",
        risk_rationale="Preliminary rating; a governance reviewer must confirm it.",
        findings=findings,
        next_actions=["Name a business owner."],
        follow_up_questions=["Who approves deployment?"],
    )
    data.update(overrides)
    return AgentAssessment(**data)


def with_finding(assessment: AgentAssessment, requirement_id: str, **changes) -> AgentAssessment:
    """Return the assessment with one finding's fields replaced."""
    for finding in assessment.findings:
        if finding.requirement_id == requirement_id:
            for key, value in changes.items():
                setattr(finding, key, value)
    return assessment


class FakeClient:
    """Returns scripted responses in order and records every request."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs):
        self.requests.append(kwargs)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def stop_turn(stop_reason: str):
    """A final turn with no usable assessment, such as a refusal or truncation."""
    return SimpleNamespace(stop_reason=stop_reason, content=[], parsed_output=None, model="fake-model")

"""A scripted stand-in for the Anthropic client so the workflow can be tested offline."""
from types import SimpleNamespace

from app.requirements_catalog import REQUIREMENT_IDS
from app.schemas import AgentAssessment, Finding

HR_SCENARIO = (
    "HR wants to use an AI system to analyze employee performance information and automatically "
    "recommend employees for promotion. The system will process employee performance records and HR "
    "information. HR intends for the AI system's recommendation to be used as the primary input into "
    "promotion decisions."
)


def tool_use(name: str, tool_id: str, args: dict | None = None):
    return SimpleNamespace(type="tool_use", name=name, id=tool_id, input=args or {})


def tool_turn(*blocks):
    return SimpleNamespace(stop_reason="tool_use", content=list(blocks), parsed_output=None, model="fake-model")


def final_turn(assessment: AgentAssessment):
    return SimpleNamespace(stop_reason="end_turn", content=[], parsed_output=assessment, model="fake-model")


def make_assessment(**overrides) -> AgentAssessment:
    findings = [
        Finding(requirement_id=rid, status="needs_clarification", evidence=[],
                explanation="Not described.", recommendation="Document this control.")
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

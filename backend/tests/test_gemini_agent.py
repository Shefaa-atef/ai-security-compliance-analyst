"""Gemini adapter tests use typed SDK responses; no provider call or key is needed."""

from types import SimpleNamespace

import httpx
import pytest
from google.genai import types

from app.agent import AssessmentUnavailable
from app.agent.gemini import GeminiAssessmentAgent
from app.governance.use_cases import CUSTOMER_SUPPORT
from tests.fakes import make_assessment


def turn(*calls):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(function_call=types.FunctionCall(name=name, args=args))
                        for name, args in calls
                    ],
                )
            )
        ]
    )


class GeminiFake:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.models = SimpleNamespace(generate_content=self.generate)

    def generate(self, **kwargs):
        self.requests.append(kwargs)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def policy_turn():
    return turn(
        ("list_requirements", {}),
        ("get_requirement_guidance", {"requirement_ids": ["AI-003"]}),
        ("scan_risk_signals", {}),
    )


def test_gemini_uses_local_tools_before_returning_a_valid_assessment():
    client = GeminiFake([policy_turn(), turn(("submit_assessment", make_assessment().model_dump()))])
    result = GeminiAssessmentAgent(client, "fake-gemini").run(CUSTOMER_SUPPORT.text)
    assert result.model == "fake-gemini"
    assert len(result.assessment.findings) == 8
    assert {call["tool"] for call in result.tool_calls} == {
        "list_requirements",
        "get_requirement_guidance",
        "scan_risk_signals",
    }
    initial_tools = client.requests[0]["config"].tools[0].function_declarations
    assert "submit_assessment" not in {tool.name for tool in initial_tools}
    final_tools = client.requests[1]["config"].tools[0].function_declarations
    assert "submit_assessment" in {tool.name for tool in final_tools}


def test_gemini_cannot_skip_policy_lookup():
    client = GeminiFake([turn(("submit_assessment", make_assessment().model_dump()))])
    with pytest.raises(AssessmentUnavailable):
        GeminiAssessmentAgent(client, "fake", max_turns=1).run(CUSTOMER_SUPPORT.text)


def test_gemini_rejects_malformed_final_output():
    client = GeminiFake([policy_turn(), turn(("submit_assessment", {"summary": "Incomplete"}))])
    with pytest.raises(AssessmentUnavailable):
        GeminiAssessmentAgent(client, "fake").run(CUSTOMER_SUPPORT.text)


def test_gemini_network_timeout_is_safe_unavailable():
    client = GeminiFake([httpx.ReadTimeout("Provider content must not reach the API response")])
    with pytest.raises(AssessmentUnavailable, match="AI provider request failed"):
        GeminiAssessmentAgent(client, "fake").run(CUSTOMER_SUPPORT.text)


def test_gemini_rejects_empty_response():
    client = GeminiFake([types.GenerateContentResponse(candidates=[])])
    with pytest.raises(AssessmentUnavailable):
        GeminiAssessmentAgent(client, "fake").run(CUSTOMER_SUPPORT.text)


def test_gemini_deadline_prevents_network_call():
    client = GeminiFake([])
    with pytest.raises(AssessmentUnavailable):
        GeminiAssessmentAgent(client, "fake", deadline_seconds=0).run(CUSTOMER_SUPPORT.text)
    assert client.requests == []

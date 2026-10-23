"""The agent loop, with a scripted model."""

import json

import anthropic
import httpx
import pytest

from app.agent import AssessmentAgent, AssessmentUnavailable
from app.governance.use_cases import HR_PROMOTIONS
from tests.fakes import FakeClient, final_turn, make_assessment, stop_turn, tool_turn, tool_use


def test_agent_runs_tools_then_returns_structured_assessment():
    client = FakeClient(
        [
            tool_turn(tool_use("list_requirements", "t1"), tool_use("scan_risk_signals", "t2")),
            tool_turn(tool_use("get_requirement_guidance", "t3", {"requirement_ids": ["AI-003", "AI-008"]})),
            final_turn(make_assessment()),
        ]
    )
    run = AssessmentAgent(client, "fake-model").run(HR_PROMOTIONS.text)

    called = [call["tool"] for call in run.tool_calls]
    assert called == ["list_requirements", "scan_risk_signals", "get_requirement_guidance"]
    assert len(run.assessment.findings) == 8

    # Both results from the first turn go back in one user message: [scenario, tool calls, results, ...]
    results = client.requests[1]["messages"][2]["content"]
    assert [result["tool_use_id"] for result in results] == ["t1", "t2"]
    scan = json.loads(results[1]["content"])
    assert scan["minimum_risk_level"] == "high"
    assert "employment_decision" in scan["signals"]


def test_scenario_is_wrapped_as_untrusted_data():
    client = FakeClient([final_turn(make_assessment())])
    AssessmentAgent(client, "fake-model").run(HR_PROMOTIONS.text)
    first_message = client.requests[0]["messages"][0]["content"]
    assert first_message.startswith("<scenario>")
    assert HR_PROMOTIONS.text in first_message


def test_unknown_tool_is_reported_to_the_model_not_raised():
    client = FakeClient([tool_turn(tool_use("delete_database", "t1")), final_turn(make_assessment())])
    run = AssessmentAgent(client, "fake-model").run(HR_PROMOTIONS.text)
    assert run.tool_calls[0]["is_error"] is True


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_unusable_stop_reasons_raise_unavailable(stop_reason):
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient([stop_turn(stop_reason)]), "m").run(HR_PROMOTIONS.text)


def test_output_that_does_not_match_the_schema_raises_unavailable():
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient([stop_turn("end_turn")]), "m").run(HR_PROMOTIONS.text)


def test_provider_timeout_raises_unavailable():
    timeout = anthropic.APITimeoutError(
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient([timeout]), "m").run(HR_PROMOTIONS.text)


def test_turn_limit_stops_a_looping_agent():
    looping = [tool_turn(tool_use("list_requirements", f"t{i}")) for i in range(3)]
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient(looping), "m", max_turns=3).run(HR_PROMOTIONS.text)


def test_time_budget_stops_the_agent_before_calling_the_model():
    client = FakeClient([])
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(client, "m", deadline_seconds=0).run(HR_PROMOTIONS.text)
    assert client.requests == []

import json

import pytest

from app.agent import AssessmentAgent, AssessmentUnavailable
from tests.fakes import HR_SCENARIO, FakeClient, final_turn, make_assessment, tool_turn, tool_use


def test_agent_runs_tools_then_returns_structured_assessment():
    client = FakeClient([
        tool_turn(tool_use("list_requirements", "t1"), tool_use("scan_risk_signals", "t2")),
        tool_turn(tool_use("get_requirement_guidance", "t3", {"requirement_ids": ["AI-003", "AI-008"]})),
        final_turn(make_assessment()),
    ])
    run = AssessmentAgent(client, "fake-model").run(HR_SCENARIO)

    assert [c["tool"] for c in run.tool_calls] == ["list_requirements", "scan_risk_signals", "get_requirement_guidance"]
    assert len(run.assessment.findings) == 8

    # Both results from the first turn go back in a single user message.
    # messages: [scenario, assistant tool calls, tool results, ...]
    results = client.requests[1]["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["t1", "t2"]
    scan = json.loads(results[1]["content"])
    assert scan["minimum_risk_level"] == "high"
    assert "employment_decision" in scan["signals"]


def test_scenario_is_wrapped_as_untrusted_data():
    client = FakeClient([final_turn(make_assessment())])
    AssessmentAgent(client, "fake-model").run(HR_SCENARIO)
    first = client.requests[0]["messages"][0]["content"]
    assert first.startswith("<scenario>") and HR_SCENARIO in first


def test_unknown_tool_is_reported_to_model_not_raised():
    client = FakeClient([tool_turn(tool_use("delete_database", "t1")), final_turn(make_assessment())])
    run = AssessmentAgent(client, "fake-model").run(HR_SCENARIO)
    assert run.tool_calls[0]["is_error"] is True


def test_refusal_and_turn_limit_raise_unavailable():
    from types import SimpleNamespace
    refusal = SimpleNamespace(stop_reason="refusal", content=[], parsed_output=None, model="m")
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient([refusal]), "m").run(HR_SCENARIO)

    looping = [tool_turn(tool_use("list_requirements", f"t{i}")) for i in range(3)]
    with pytest.raises(AssessmentUnavailable):
        AssessmentAgent(FakeClient(looping), "m", max_turns=3).run(HR_SCENARIO)

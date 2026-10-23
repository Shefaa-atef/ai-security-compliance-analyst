import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.agent import AssessmentAgent
from app.governance.use_cases import HR_PROMOTIONS
from app.rate_limit import RateLimiter
from tests.fakes import FakeClient, final_turn, make_assessment, tool_turn, tool_use

ZERO_WIDTH_SPACE = chr(0x200B)


@pytest.fixture
def api(tmp_path, monkeypatch):
    audit_file = tmp_path / "audit.jsonl"
    monkeypatch.setattr(main.settings, "audit_log_path", str(audit_file))
    monkeypatch.setattr(main, "limiter", RateLimiter(100))
    scripted = {"responses": []}
    main.app.dependency_overrides[main.get_agent] = lambda: AssessmentAgent(FakeClient(scripted["responses"]), "fake-model")
    yield TestClient(main.app), scripted, audit_file
    main.app.dependency_overrides.clear()


def test_assess_returns_contract_shape_and_audit_entry(api):
    client, scripted, audit_file = api
    scripted["responses"][:] = [
        tool_turn(tool_use("list_requirements", "t1"), tool_use("scan_risk_signals", "t2")),
        final_turn(make_assessment(risk_level="low")),
    ]
    res = client.post("/api/assess", json={"scenario": HR_PROMOTIONS.text + " Contact hr.lead@acme.com."})
    assert res.status_code == 200
    body = res.json()

    # Fields required by frontend/src/lib/api.js validateAssessment
    for key in ("assessment_id", "summary", "risk_level", "risk_rationale", "next_actions",
                "follow_up_questions", "review_steps", "findings"):
        assert key in body
    assert len(body["findings"]) == 8
    assert body["risk_level"] == "high"  # raised by the policy floor
    assert any("redacted" in n for n in body["guardrail_notes"])
    assert any("requirement catalog" in s for s in body["review_steps"])

    entry = json.loads(audit_file.read_text().strip().splitlines()[-1])
    assert entry["outcome"] == "completed"
    assert entry["tool_calls"] == ["list_requirements", "scan_risk_signals"]
    assert "hr.lead@acme.com" not in audit_file.read_text()  # raw scenario never logged


def test_validation_errors_return_422(api):
    client, _, _ = api
    assert client.post("/api/assess", json={"scenario": "too short"}).status_code == 422
    assert client.post("/api/assess", json={"scenario": "x" * 12_001}).status_code == 422
    assert client.post("/api/assess", json={"scenario": " " * 30 + ZERO_WIDTH_SPACE * 5}).status_code == 422


def test_ai_failure_returns_503(api):
    client, scripted, audit_file = api
    from types import SimpleNamespace
    scripted["responses"][:] = [SimpleNamespace(stop_reason="refusal", content=[], parsed_output=None, model="m")]
    res = client.post("/api/assess", json={"scenario": HR_PROMOTIONS.text})
    assert res.status_code == 503
    assert json.loads(audit_file.read_text().splitlines()[-1])["outcome"] == "ai_unavailable"


def test_rate_limit_returns_429(api, monkeypatch):
    client, scripted, _ = api
    monkeypatch.setattr(main, "limiter", RateLimiter(1))
    scripted["responses"][:] = [final_turn(make_assessment())]
    assert client.post("/api/assess", json={"scenario": HR_PROMOTIONS.text}).status_code == 200
    assert client.post("/api/assess", json={"scenario": HR_PROMOTIONS.text}).status_code == 429


def test_missing_api_key_returns_503(monkeypatch):
    monkeypatch.setattr(main.settings, "anthropic_api_key", None)
    res = TestClient(main.app).post("/api/assess", json={"scenario": HR_PROMOTIONS.text})
    assert res.status_code == 503

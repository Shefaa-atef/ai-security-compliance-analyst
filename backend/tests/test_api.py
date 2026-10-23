"""The HTTP contract the frontend relies on."""

from app.api.dependencies import get_agent
from app.governance.use_cases import HR_PROMOTIONS
from tests.fakes import final_turn, make_assessment, stop_turn, tool_turn, tool_use

ZERO_WIDTH_SPACE = chr(0x200B)

# Fields required by validateAssessment in frontend/src/lib/api.js
CONTRACT_FIELDS = {
    "assessment_id",
    "summary",
    "risk_level",
    "risk_rationale",
    "findings",
    "next_actions",
    "follow_up_questions",
    "review_steps",
}


def test_assess_returns_the_contract_and_writes_an_audit_entry(api):
    api.responses[:] = [
        tool_turn(tool_use("list_requirements", "t1"), tool_use("scan_risk_signals", "t2")),
        final_turn(make_assessment(risk_level="low")),
    ]
    res = api.post(HR_PROMOTIONS.text + " Contact hr.lead@acme.com.")
    body = res.json()

    assert res.status_code == 200
    assert body.keys() >= CONTRACT_FIELDS
    assert len(body["findings"]) == 8
    assert body["risk_level"] == "high"  # raised by the policy floor
    assert any("redacted" in note for note in body["guardrail_notes"])

    entry = api.last_audit_entry()
    assert entry["outcome"] == "completed"
    assert entry["request_id"] == res.headers["X-Request-ID"]
    assert entry["tool_calls"] == ["list_requirements", "scan_risk_signals"]
    assert "hr.lead@acme.com" not in api.audit_file.read_text(encoding="utf-8")


def test_invalid_input_returns_a_safe_422(api):
    res = api.post("password: hunter2")
    body = res.json()
    assert res.status_code == 422
    assert body["request_id"] == res.headers["X-Request-ID"]
    assert "hunter2" not in res.text


def test_length_limits_apply_after_trimming(api):
    api.responses[:] = [final_turn(make_assessment())]
    assert api.post("x" * 12_001).status_code == 422
    assert api.post("   short text   " + " " * 50).status_code == 422
    assert api.post(" " * 30 + ZERO_WIDTH_SPACE * 5).status_code == 422
    assert api.post(" " * 100 + HR_PROMOTIONS.text + " " * 100).status_code == 200


def test_malformed_requests_return_422(api):
    assert api.client.post("/api/assess", json={"wrong": "field"}).status_code == 422
    not_json = api.client.post(
        "/api/assess", content="not json", headers={"Content-Type": "application/json"}
    )
    assert not_json.status_code == 422


def test_ai_failure_returns_503_and_is_audited(api):
    api.responses[:] = [stop_turn("refusal")]
    assert api.post(HR_PROMOTIONS.text).status_code == 503
    assert api.last_audit_entry()["outcome"] == "ai_unavailable"


def test_rate_limit_returns_429(api):
    api.limiter.limit = 1
    api.responses[:] = [final_turn(make_assessment())]
    assert api.post(HR_PROMOTIONS.text).status_code == 200
    assert api.post(HR_PROMOTIONS.text).status_code == 429


def test_missing_api_key_returns_503(api):
    api.settings.anthropic_api_key = None
    del api.client.app.dependency_overrides[get_agent]  # use the real dependency
    assert api.post(HR_PROMOTIONS.text).status_code == 503


def test_health_exposes_no_configuration(api):
    assert api.client.get("/api/health").json() == {"status": "ok", "ai_configured": True}

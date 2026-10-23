from app.governance import risk_signals
from app.governance.use_cases import CUSTOMER_SUPPORT, HR_PROMOTIONS, SECURITY_ASSISTANT
from app.guardrails import output as output_guardrails
from app.schemas import Finding
from tests.fakes import make_assessment, with_finding


def run(assessment, scenario):
    return output_guardrails.apply(assessment, scenario, risk_signals.scan(scenario))


def test_invented_quotes_are_removed_and_real_ones_kept():
    a = with_finding(
        make_assessment(),
        "AI-003",
        status="supported",
        evidence=[
            "A human support agent will review the generated response before sending it to the customer.",
            "All responses are approved by a compliance officer.",
        ],
    )
    result = run(a, CUSTOMER_SUPPORT.text)
    f = result.assessment.findings[2]
    assert f.status == "supported"
    assert f.evidence == [
        "A human support agent will review the generated response before sending it to the customer"
    ]
    assert result.corrections.quotes_removed == 1


def test_supported_without_evidence_is_downgraded():
    a = with_finding(make_assessment(), "AI-001", status="supported", evidence=["The CISO owns this system."])
    result = run(a, CUSTOMER_SUPPORT.text)
    assert result.assessment.findings[0].status == "needs_clarification"
    assert any("AI-001" in n for n in result.corrections.notes)


def test_missing_duplicate_and_unknown_findings_are_normalized():
    a = make_assessment()
    a.findings = [
        a.findings[1],
        a.findings[1],
        Finding(requirement_id="AI-999", status="gap", evidence=[], explanation="x", recommendation="y"),
    ]
    result = run(a, CUSTOMER_SUPPORT.text)
    ids = [f.requirement_id for f in result.assessment.findings]
    assert ids == [f"AI-00{i}" for i in range(1, 9)]
    assert any("did not assess" in n for n in result.corrections.notes)


def test_automated_hr_decision_forces_oversight_gap_and_high_risk():
    a = with_finding(make_assessment(risk_level="low"), "AI-003", status="needs_clarification")
    result = run(a, HR_PROMOTIONS.text)
    assert result.assessment.findings[2].status == "gap"
    assert result.assessment.risk_level == "high"
    assert "Policy minimum applied" in result.assessment.risk_rationale


def test_human_review_scenario_is_not_forced_to_gap():
    a = with_finding(
        make_assessment(),
        "AI-003",
        status="supported",
        evidence=[
            "A human support agent will review the generated response before sending it to the customer."
        ],
    )
    result = run(a, CUSTOMER_SUPPORT.text)
    assert result.assessment.findings[2].status == "supported"


def test_third_party_cannot_be_not_applicable():
    a = with_finding(make_assessment(), "AI-006", status="not_applicable")
    result = run(a, CUSTOMER_SUPPORT.text)
    assert result.assessment.findings[5].status == "needs_clarification"


def test_risk_is_never_lowered_by_guardrails():
    result = run(make_assessment(risk_level="high"), CUSTOMER_SUPPORT.text)
    assert result.assessment.risk_level == "high"
    assert not any("Risk level raised" in n for n in result.corrections.notes)


def test_curly_apostrophes_in_quotes_still_verify():
    curly = "deployed within the organization" + chr(0x2019) + "s cloud environment"
    a = with_finding(make_assessment(), "AI-005", evidence=[curly])
    result = run(a, SECURITY_ASSISTANT.text)
    assert result.assessment.findings[4].evidence == ["deployed within the organization's cloud environment"]

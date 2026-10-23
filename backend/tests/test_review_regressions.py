from app.governance import risk_signals
from app.guardrails import output
from tests.fakes import make_assessment, with_finding


def assess(scenario, assessment=None):
    return output.apply(assessment or make_assessment(), scenario, risk_signals.scan(scenario)).assessment


def test_negated_human_review_is_not_an_oversight_control():
    scenario = "An AI system automatically approves customer account changes with no human review."
    signals = risk_signals.scan(scenario)
    assert "no_human_review" in signals
    assert "human_review" not in signals
    result = assess(scenario)
    assert result.findings[2].status == "gap"


def test_explicit_reviewer_negation_is_not_counted_as_human_review():
    signals = risk_signals.scan("A human will not review the recommendations before use.")
    assert "human_review" not in signals


def test_automatic_summarization_is_not_an_automated_business_decision():
    signals = risk_signals.scan(
        "The assistant automatically summarizes customer names and conversation history. "
        "A human agent reviews every response before sending it."
    )
    assert "automated_decision" not in signals
    assert risk_signals.risk_floor(signals)[0] == "medium"


def test_vague_scenario_preserves_unknown_risk():
    result = assess(
        "We plan to build an AI assistant; its purpose has not yet been decided.",
        make_assessment(risk_level="unknown"),
    )
    assert result.risk_level == "unknown"


def test_high_risk_review_is_applicable_even_when_an_unrelated_quote_exists():
    scenario = "HR uses AI to recommend promotions based on employee records."
    assessment = with_finding(
        make_assessment(risk_level="high"), "AI-008", status="not_applicable", evidence=["employee records"]
    )
    result = assess(scenario, assessment)
    assert result.findings[7].status == "needs_clarification"


def test_evidence_is_returned_as_exact_source_text_after_tolerant_matching():
    scenario = "Security analysts will  review recommendations before taking action."
    assessment = with_finding(
        make_assessment(),
        "AI-003",
        status="supported",
        evidence=["SECURITY ANALYSTS will review recommendations"],
    )
    result = assess(scenario, assessment)
    quote = result.findings[2].evidence[0]
    assert quote == "Security analysts will  review recommendations"
    assert quote in scenario


def test_corrected_finding_does_not_claim_the_original_control_is_supported():
    scenario = "An internal assistant is planned but its controls have not been described."
    assessment = with_finding(
        make_assessment(),
        "AI-001",
        status="supported",
        evidence=[],
        explanation="The owner is clearly identified.",
        recommendation="No action needed.",
    )
    finding = assess(scenario, assessment).findings[0]
    assert finding.status == "needs_clarification"
    assert "without evidence" in finding.explanation
    assert finding.recommendation != "No action needed."


def test_no_human_resources_data_is_not_a_signal_of_automated_decisions():
    signals = risk_signals.scan("This assistant handles security alerts and no human resources data.")
    assert "automated_decision" not in signals

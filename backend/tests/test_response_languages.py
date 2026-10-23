"""Language is controlled by a validated request field, never by scenario instructions."""

import re
from string import Formatter

from app.agent import AssessmentAgent
from app.agent.gemini import GeminiAssessmentAgent
from app.governance.use_cases import CUSTOMER_SUPPORT
from app.guardrails import output
from app.guardrails.input import prepare_input
from app.i18n import CATALOGS
from tests.fakes import FakeClient, final_turn, make_assessment, with_finding
from tests.test_gemini_agent import GeminiFake, policy_turn, turn


def test_backend_catalogs_have_matching_keys_and_placeholders():
    formatter = Formatter()
    reference = CATALOGS["en"]
    for catalog in CATALOGS.values():
        assert catalog.keys() == reference.keys()
        for key, message in catalog.items():
            assert message.strip()

            def fields(value):
                return {name for _, name, _, _ in formatter.parse(value) if name}

            assert fields(message) == fields(reference[key])


def test_both_provider_prompts_request_arabic_without_translating_evidence():
    claude = FakeClient([final_turn(make_assessment())])
    AssessmentAgent(claude, "fake").run(CUSTOMER_SUPPORT.text, response_language="ar")
    assert "Modern Standard Arabic" in claude.requests[0]["system"]
    assert "Never translate evidence" in claude.requests[0]["system"]
    gemini = GeminiFake([policy_turn(), turn(("submit_assessment", make_assessment().model_dump()))])
    GeminiAssessmentAgent(gemini, "fake").run(CUSTOMER_SUPPORT.text, response_language="ar")
    assert "Modern Standard Arabic" in gemini.requests[0]["config"].system_instruction


def test_arabic_request_returns_metadata_and_localized_actual_activity(api):
    api.responses[:] = [final_turn(make_assessment())]
    response = api.client.post(
        "/api/assess", json={"scenario": CUSTOMER_SUPPORT.text, "response_language": "ar"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["response_language"] == "ar"
    assert all(re.search(r"[\u0600-\u06ff]", step) for step in body["review_steps"])
    assert api.last_audit_entry()["response_language"] == "ar"


def test_unsupported_response_language_is_rejected(api):
    response = api.client.post(
        "/api/assess", json={"scenario": CUSTOMER_SUPPORT.text, "response_language": "fr"}
    )
    assert response.status_code == 422


def test_arabic_guardrail_corrections_do_not_change_source_evidence():
    quote = "A human support agent will review the generated response before sending it to the customer"
    assessment = with_finding(make_assessment(), "AI-003", status="supported", evidence=[quote])
    assessment = with_finding(assessment, "AI-001", status="supported", evidence=[])
    result = output.apply(assessment, CUSTOMER_SUPPORT.text, {}, response_language="ar")
    assert result.assessment.findings[2].evidence == [quote]
    corrected = result.assessment.findings[0]
    assert re.search(r"[\u0600-\u06ff]", corrected.explanation)
    assert re.search(r"[\u0600-\u06ff]", corrected.recommendation)
    assert corrected.status == "needs_clarification"
    assert all(re.search(r"[\u0600-\u06ff]", note) for note in result.corrections.notes)


def test_arabic_redaction_notes_are_localized():
    prepared = prepare_input("Contact fictional.user@example.com about the proposed internal AI assistant.")
    assert "بريد إلكتروني" in prepared.localized_notes("ar")[0]
    assert "fictional.user@example.com" not in prepared.localized_notes("ar")[0]

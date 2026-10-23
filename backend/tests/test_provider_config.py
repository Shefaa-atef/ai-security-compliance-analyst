import pytest
from fastapi import HTTPException

from app.agent.gemini import GeminiAssessmentAgent
from app.api import dependencies
from app.config import Settings


def test_gemini_uses_only_its_own_key_and_model(monkeypatch):
    settings = Settings(
        _env_file=None,
        ai_provider="gemini",
        gemini_api_key="gemini-test-key",
        anthropic_api_key="another-test-key",
        gemini_model="fake-gemini",
    )
    client = object()
    received = []

    def fake_client(key):
        received.append(key)
        return client

    monkeypatch.setattr(dependencies, "_gemini_client", fake_client)
    agent = dependencies.get_agent(settings)
    assert isinstance(agent, GeminiAssessmentAgent)
    assert agent.client is client
    assert agent.model == "fake-gemini"
    assert received == ["gemini-test-key"]


def test_missing_gemini_key_does_not_silently_use_anthropic_credentials():
    settings = Settings(_env_file=None, ai_provider="gemini", anthropic_api_key="another-test-key")
    assert settings.configured_api_key is None
    with pytest.raises(HTTPException) as error:
        dependencies.get_agent(settings)
    assert error.value.status_code == 503


def test_health_reflects_the_selected_provider(api):
    api.settings.ai_provider = "gemini"
    api.settings.gemini_api_key = None
    assert api.client.get("/api/health").json() == {"status": "ok", "ai_configured": False}
    api.settings.gemini_api_key = "test-key"
    assert api.client.get("/api/health").json() == {"status": "ok", "ai_configured": True}

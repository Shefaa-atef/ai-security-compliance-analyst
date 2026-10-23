"""Shared fixtures: an API client whose model, settings and rate limiter are replaced."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent import AssessmentAgent
from app.api.dependencies import get_agent, get_limiter
from app.config import Settings, get_settings
from app.main import app
from app.rate_limit import RateLimiter
from tests.fakes import FakeClient


@dataclass
class ApiHarness:
    client: TestClient
    settings: Settings
    limiter: RateLimiter
    audit_file: Path
    # Scripted model responses for the next request, consumed in order.
    responses: list = field(default_factory=list)

    def post(self, scenario: str):
        return self.client.post("/api/assess", json={"scenario": scenario})

    def last_audit_entry(self) -> dict:
        return json.loads(self.audit_file.read_text(encoding="utf-8").splitlines()[-1])


@pytest.fixture
def api(tmp_path):
    settings = Settings(
        _env_file=None, anthropic_api_key="test-key", audit_log_path=str(tmp_path / "audit.jsonl")
    )
    harness = ApiHarness(
        client=TestClient(app),
        settings=settings,
        limiter=RateLimiter(100),
        audit_file=tmp_path / "audit.jsonl",
    )
    app.dependency_overrides[get_settings] = lambda: harness.settings
    app.dependency_overrides[get_limiter] = lambda: harness.limiter
    app.dependency_overrides[get_agent] = lambda: AssessmentAgent(FakeClient(harness.responses), "fake-model")
    yield harness
    app.dependency_overrides.clear()

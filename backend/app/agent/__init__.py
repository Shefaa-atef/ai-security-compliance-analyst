"""Shared interface for the tool-using assessment providers."""

from typing import Protocol

from ..i18n import ResponseLanguage
from .runner import AgentRun, AssessmentAgent, AssessmentUnavailable

__all__ = ["AgentRun", "AssessmentAgent", "AssessmentRunner", "AssessmentUnavailable"]


class AssessmentRunner(Protocol):
    def run(self, scenario: str, response_language: ResponseLanguage = "en") -> AgentRun: ...

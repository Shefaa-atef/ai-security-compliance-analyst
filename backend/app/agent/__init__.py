"""Shared interface for the tool-using assessment providers."""

from typing import Protocol

from .runner import AgentRun, AssessmentAgent, AssessmentUnavailable

__all__ = ["AgentRun", "AssessmentAgent", "AssessmentRunner", "AssessmentUnavailable"]


class AssessmentRunner(Protocol):
    def run(self, scenario: str) -> AgentRun: ...

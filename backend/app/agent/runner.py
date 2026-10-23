"""The agent loop.

Claude receives the scenario as untrusted data plus the tools. Each turn it
either calls tools, whose results are sent back, or returns the final
assessment, which structured outputs force to match `AgentAssessment`. The
loop is bounded by a turn limit and an overall time budget.
"""

import json
import logging
import time
from dataclasses import dataclass, field

import anthropic
from pydantic import ValidationError

from ..i18n import ResponseLanguage
from ..schemas import AgentAssessment
from .prompt import system_prompt, user_message
from .tools import TOOL_DEFINITIONS, run_tool

log = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 16_000
MIN_SECONDS_FOR_A_TURN = 3


class AssessmentUnavailable(Exception):
    """The AI service could not produce a usable assessment."""


@dataclass
class AgentRun:
    assessment: AgentAssessment
    model: str
    tool_calls: list[dict] = field(default_factory=list)


class AssessmentAgent:
    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str,
        max_turns: int = 6,
        deadline_seconds: float = 55.0,
    ):
        self.client = client
        self.model = model
        self.max_turns = max_turns
        self.deadline_seconds = deadline_seconds

    def run(self, scenario: str, response_language: ResponseLanguage = "en") -> AgentRun:
        deadline = time.monotonic() + self.deadline_seconds
        messages: list[dict] = [{"role": "user", "content": user_message(scenario)}]
        tool_calls: list[dict] = []

        for _ in range(self.max_turns):
            remaining = deadline - time.monotonic()
            if remaining < MIN_SECONDS_FOR_A_TURN:
                raise AssessmentUnavailable("Assessment exceeded its time budget")

            response = self._request(messages, timeout=remaining, response_language=response_language)

            if response.stop_reason == "tool_use":
                # Append the full content so thinking blocks are passed back unchanged.
                messages.append({"role": "assistant", "content": response.content})
                messages.append(
                    {"role": "user", "content": self._run_tools(response.content, scenario, tool_calls)}
                )
                continue

            if response.parsed_output is None:
                raise AssessmentUnavailable("AI response did not match the assessment schema")
            return AgentRun(assessment=response.parsed_output, model=response.model, tool_calls=tool_calls)

        raise AssessmentUnavailable("Agent did not finish within the turn limit")

    def _request(self, messages: list[dict], timeout: float, response_language: ResponseLanguage = "en"):
        try:
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system_prompt(response_language),
                tools=TOOL_DEFINITIONS,
                messages=messages,
                output_format=AgentAssessment,
                output_config={"effort": "medium"},
                timeout=timeout,
                # Server-side refusal fallback: if a safety classifier declines, the API
                # retries on Anthropic's recommended fallback model within the same call.
                extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
                extra_body={"fallbacks": "default"},
            )
        except (
            anthropic.APIConnectionError,
            anthropic.APIStatusError,
            anthropic.APIResponseValidationError,
            ValidationError,
        ) as exc:
            # Log the error type and status only; provider messages may echo request content.
            log.warning(
                "Claude API call failed: %s status=%s", type(exc).__name__, getattr(exc, "status_code", None)
            )
            raise AssessmentUnavailable("AI provider request failed") from exc

        if response.stop_reason == "refusal":
            raise AssessmentUnavailable("AI provider declined the request")
        if response.stop_reason == "max_tokens":
            raise AssessmentUnavailable("AI response was truncated")
        return response

    @staticmethod
    def _run_tools(content: list, scenario: str, tool_calls: list[dict]) -> list[dict]:
        """Run every tool call in one turn and return all results in a single message."""
        results = []
        for block in content:
            if block.type != "tool_use":
                continue
            try:
                output, is_error = run_tool(block.name, block.input or {}, scenario), False
            except Exception as exc:  # report tool failures to the model instead of failing the request
                output, is_error = {"error": str(exc)}, True
            tool_calls.append({"tool": block.name, "input": block.input, "is_error": is_error})
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                    "is_error": is_error,
                }
            )
        return results

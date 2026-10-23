"""Gemini tool-use adapter; shares the same local tools and output guardrails."""

import logging
import time

import httpx
from google.genai import errors, types
from pydantic import ValidationError

from ..i18n import ResponseLanguage
from ..schemas import AgentAssessment
from .prompt import system_prompt, user_message
from .runner import AgentRun, AssessmentUnavailable
from .tools import TOOL_DEFINITIONS, run_tool

log = logging.getLogger(__name__)
_REQUIRED_TOOLS = {"list_requirements", "get_requirement_guidance", "scan_risk_signals"}
_FINAL_TOOL = "submit_assessment"


class GeminiAssessmentAgent:
    def __init__(self, client, model: str, max_turns: int = 6, deadline_seconds: float = 55):
        self.client = client
        self.model = model
        self.max_turns = max_turns
        self.deadline_seconds = deadline_seconds

    def run(self, scenario: str, response_language: ResponseLanguage = "en") -> AgentRun:
        deadline = time.monotonic() + self.deadline_seconds
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message(scenario))])]
        tool_calls: list[dict] = []
        completed: set[str] = set()
        for _ in range(self.max_turns):
            remaining = deadline - time.monotonic()
            if remaining < 3:
                raise AssessmentUnavailable("Assessment exceeded its time budget")
            response = self._request(contents, completed, remaining, response_language)
            calls = response.function_calls or []
            if not calls or not response.candidates:
                raise AssessmentUnavailable("Gemini did not return a usable tool response")
            contents.append(response.candidates[0].content)
            results = []
            for call in calls:
                if call.name == _FINAL_TOOL and completed >= _REQUIRED_TOOLS:
                    try:
                        assessment = AgentAssessment.model_validate(dict(call.args or {}))
                    except ValidationError as exc:
                        raise AssessmentUnavailable("Gemini returned an invalid assessment") from exc
                    return AgentRun(
                        assessment=assessment,
                        model=response.model_version or self.model,
                        tool_calls=tool_calls,
                    )
                try:
                    result = run_tool(call.name, dict(call.args or {}), scenario)
                    is_error = False
                    completed.add(call.name)
                except (ValueError, TypeError, KeyError):
                    result, is_error = {"error": "Invalid local tool call."}, True
                tool_calls.append({"tool": call.name, "input": dict(call.args or {}), "is_error": is_error})
                results.append(types.Part.from_function_response(name=call.name, response={"result": result}))
            contents.append(types.Content(role="user", parts=results))
        raise AssessmentUnavailable("Gemini did not finish within the turn limit")

    def _request(
        self, contents: list, completed: set[str], remaining: float, response_language: ResponseLanguage
    ):
        declarations = [
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema=tool["input_schema"],
            )
            for tool in TOOL_DEFINITIONS
        ]
        if completed >= _REQUIRED_TOOLS:
            declarations.append(
                types.FunctionDeclaration(
                    name=_FINAL_TOOL,
                    description="Return the evidence-linked assessment after gathering policy context.",
                    parameters_json_schema=AgentAssessment.model_json_schema(),
                )
            )
        try:
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt(response_language),
                    tools=[types.Tool(function_declarations=declarations)],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(mode="ANY")
                    ),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    max_output_tokens=8192,
                    http_options=types.HttpOptions(timeout=int(remaining * 1000)),
                ),
            )
        except (errors.APIError, httpx.HTTPError, ValidationError) as exc:
            log.warning("Gemini request failed: %s status=%s", type(exc).__name__, getattr(exc, "code", None))
            raise AssessmentUnavailable("AI provider request failed") from exc

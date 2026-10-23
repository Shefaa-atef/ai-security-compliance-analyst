"""Deterministic risk-signal scan.

Used two ways: the agent calls it as a tool to ground its reasoning, and the
output guardrails use it to enforce minimum risk levels the model cannot
talk its way below.
"""
import re

_SIGNALS: dict[str, tuple[str, str]] = {
    "personal_data": (
        "Personal information about customers or employees",
        r"customer names?|personal (data|information)|\bpii\b|employee (records?|information|data)"
        r"|conversation history|performance (records?|information)|hr information",
    ),
    "financial_data": (
        "Financial or account information",
        r"account (information|details|numbers?)|financial|payment|transaction|credit|bank",
    ),
    "security_data": (
        "Security logs, alerts or threat intelligence",
        r"security (logs?|alerts?|events?)|threat intelligence|\bsiem\b|vulnerabilit",
    ),
    "employment_decision": (
        "Decisions about employees (hiring, promotion, pay, termination)",
        r"promot|hiring|recruit|terminat|dismiss|salary|compensation|performance review",
    ),
    "automated_decision": (
        "AI output drives a decision with little or no human judgment",
        r"automatic(ally)?|primary input|without (human )?review|no human|auto-?(approve|reject)|fully automated",
    ),
    "human_review": (
        "A person reviews AI output before it is used",
        r"(human|agent|analyst|person|staff|reviewer)s?\b.{0,40}\breview|review.{0,40}before (sending|taking|use|acting)",
    ),
    "third_party": (
        "A third-party model, API or external service is used",
        r"third[- ]party|hosted (llm|model|api)|external (api|provider|vendor|service)|vendor|saas",
    ),
    "internal_deployment": (
        "Deployed inside the organization's environment",
        r"internal(ly)?|within the organi[sz]ation|on[- ]prem",
    ),
}
_COMPILED = {key: re.compile(pattern, re.I) for key, (_, pattern) in _SIGNALS.items()}

_ORDER = {"unknown": -1, "low": 0, "medium": 1, "high": 2}


def scan(text: str) -> dict[str, dict]:
    """Return the detected signals with the matched phrase as evidence."""
    found = {}
    for key, pattern in _COMPILED.items():
        if match := pattern.search(text):
            found[key] = {"description": _SIGNALS[key][0], "matched_text": match.group(0)}
    return found


def risk_floor(signals: dict) -> tuple[str, str | None]:
    """Minimum risk level implied by the signals, with the reason."""
    if "employment_decision" in signals:
        return "high", "Decisions about employees are treated as high risk."
    if "automated_decision" in signals and ({"personal_data", "financial_data"} & signals.keys()):
        return "high", "Automated decisions that use personal or financial data are treated as high risk."
    if {"personal_data", "financial_data", "security_data"} & signals.keys():
        return "medium", "Sensitive data is processed, so the risk cannot be rated low."
    return "low", None


def at_least(level: str, floor: str) -> bool:
    return _ORDER[level] >= _ORDER[floor]

"""Localize actual pipeline activity; the model cannot invent this trail."""

from .guardrails.corrections import Corrections
from .guardrails.input import PreparedInput
from .i18n import ResponseLanguage, text


def build(
    prepared: PreparedInput,
    tool_calls: list[dict],
    model: str,
    corrections: Corrections,
    language: ResponseLanguage = "en",
) -> list[str]:
    injection = text(language, "trail.injection" if prepared.injection_signals else "trail.clean")
    steps = [text(language, "trail.input", count=sum(prepared.redactions.values()), injection=injection)]
    for call in tool_calls:
        name = call["tool"]
        if call["is_error"]:
            step = text(language, "trail.failed", tool=name)
        elif name == "list_requirements":
            step = text(language, "trail.catalog")
        elif name == "get_requirement_guidance":
            ids = ", ".join(call["input"].get("requirement_ids", [])) or text(language, "none")
            step = text(language, "trail.guidance", ids=ids)
        elif name == "scan_risk_signals":
            step = text(language, "trail.scan")
        else:
            step = text(language, "trail.tool", tool=name)
        steps.append(step)
    steps.append(text(language, "trail.model", model=model))
    steps.append(
        text(
            language,
            "trail.output",
            verified=corrections.quotes_verified,
            removed=corrections.quotes_removed,
            changed=corrections.status_changes,
        )
    )
    steps.append(text(language, "trail.human"))
    return steps

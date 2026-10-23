"""Tools the agent can call, and the code that runs them.

All tools are read-only and local: they look up the requirement catalog or
scan the scenario the backend already holds. Nothing reaches the network or
runs user-supplied code.
"""

from ..governance import catalog, risk_signals

_NO_ARGS = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

TOOL_DEFINITIONS = [
    {
        "name": "list_requirements",
        "description": "List the organization's AI governance requirements (id, title, requirement text).",
        "strict": True,
        "input_schema": _NO_ARGS,
    },
    {
        "name": "get_requirement_guidance",
        "description": "Get assessment guidance for specific requirements: what evidence satisfies each "
        "one and which signals indicate a gap.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "requirement_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Requirement ids such as AI-002.",
                }
            },
            "required": ["requirement_ids"],
            "additionalProperties": False,
        },
    },
    {
        "name": "scan_risk_signals",
        "description": "Run the organization's deterministic risk-signal scan on the scenario. Returns "
        "detected data categories, third-party use, automation and decision impact, plus the minimum "
        "risk level that policy requires.",
        "strict": True,
        "input_schema": _NO_ARGS,
    },
]


def run_tool(name: str, args: dict, scenario: str) -> dict | list:
    if name == "list_requirements":
        return catalog.list_requirements()
    if name == "get_requirement_guidance":
        ids = [str(rid) for rid in args.get("requirement_ids", [])][: len(catalog.REQUIREMENT_IDS)]
        return catalog.get_guidance(ids)
    if name == "scan_risk_signals":
        # The backend scans the scenario it holds; the model cannot substitute other text.
        signals = risk_signals.scan(scenario)
        floor, reason = risk_signals.risk_floor(signals)
        return {"signals": signals, "minimum_risk_level": floor, "reason": reason}
    raise ValueError(f"Unknown tool: {name}")

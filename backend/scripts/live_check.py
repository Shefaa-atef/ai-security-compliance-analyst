"""Live check: run the three supplied use cases against the configured live AI provider.

This is separate from the pytest suite on purpose. It needs the selected provider key
(GEMINI_API_KEY or ANTHROPIC_API_KEY) in backend/.env. It costs a small amount per run,
and its results depend on the model. Run from the backend folder:

    python -m scripts.live_check
"""

import sys
import time

from app import pipeline
from app.agent import AssessmentUnavailable
from app.api.dependencies import get_agent
from app.config import get_settings
from app.governance.use_cases import USE_CASES


def main() -> int:
    settings = get_settings()
    if not settings.configured_api_key:
        print("Configure the selected provider key in backend/.env before running the live check.")
        return 1
    agent = get_agent(settings)
    failures = 0
    for use_case in USE_CASES:
        label = f"Use case {use_case.id}: {use_case.title}"
        started = time.monotonic()
        try:
            result = pipeline.assess(use_case.text, agent, "logs/live_check.jsonl")
        except AssessmentUnavailable as exc:
            failures += 1
            print(f"\n{label}: FAILED ({exc})")
            continue

        print(f"\n{label}: risk={result.risk_level} in {time.monotonic() - started:.1f}s via {result.model}")
        for finding in result.findings:
            print(f"  {finding.requirement_id} {finding.status:<20} evidence={len(finding.evidence)}")
        for note in result.guardrail_notes:
            print(f"  guardrail: {note}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

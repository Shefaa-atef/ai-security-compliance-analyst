"""Live check: run the three supplied use cases against the real Claude API.

This is separate from the pytest suite on purpose. It needs ANTHROPIC_API_KEY
in backend/.env, costs a small amount per run, and its results depend on the
model. Run from the backend folder:

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
    agent = get_agent(get_settings())
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

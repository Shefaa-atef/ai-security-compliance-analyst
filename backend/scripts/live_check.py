"""Live check: run the three supplied use cases against the real Claude API.

This is separate from the pytest suite on purpose. It needs ANTHROPIC_API_KEY
in backend/.env, costs a small amount per run, and its results depend on the
model. Run from the backend folder:

    python -m scripts.live_check
"""
import sys
import time

from app.main import get_agent
from app import service
from tests.fakes import HR_SCENARIO
from tests.test_output_guardrails import SUPPORT_SCENARIO
from tests.test_scenarios import SECURITY_SCENARIO

CASES = {
    "A - Customer support": SUPPORT_SCENARIO,
    "B - Security assistant": SECURITY_SCENARIO,
    "C - HR promotions": HR_SCENARIO,
}


def main() -> int:
    failures = 0
    for name, scenario in CASES.items():
        started = time.monotonic()
        try:
            result = service.assess(scenario, get_agent(), "logs/live_check.jsonl")
        except Exception as exc:  # report and continue with the next case
            failures += 1
            print(f"\n{name}: FAILED ({type(exc).__name__})")
            continue
        print(f"\n{name}: risk={result.risk_level} in {time.monotonic() - started:.1f}s via {result.model}")
        for f in result.findings:
            print(f"  {f.requirement_id} {f.status:<20} evidence={len(f.evidence)}")
        for note in result.guardrail_notes:
            print(f"  guardrail: {note}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

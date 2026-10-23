"""Live check: run the three supplied use cases against the real Claude API.

This is separate from the pytest suite on purpose. It needs ANTHROPIC_API_KEY
in backend/.env, costs a small amount per run, and its results depend on the
model. Run from the backend folder:

    python -m scripts.live_check
"""
import sys
import time

from app import service
from app.governance.use_cases import CUSTOMER_SUPPORT, HR_PROMOTIONS, SECURITY_ASSISTANT
from app.main import get_agent

CASES = {
    "A - Customer support": CUSTOMER_SUPPORT.text,
    "B - Security assistant": SECURITY_ASSISTANT.text,
    "C - HR promotions": HR_PROMOTIONS.text,
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

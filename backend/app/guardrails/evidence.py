"""Coverage and evidence checks on the model's findings.

These make the report traceable: every requirement is answered once, and every
quote shown as evidence really appears in the scenario.
"""

import re

from ..governance.catalog import REQUIREMENT_IDS
from ..schemas import Finding
from .corrections import Corrections

MAX_QUOTES_PER_FINDING = 3
MAX_QUOTE_CHARS = 300

# Curly quotes typed by the model are compared as straight quotes.
_QUOTE_FOLDING = str.maketrans({chr(0x2018): "'", chr(0x2019): "'", chr(0x201C): '"', chr(0x201D): '"'})


def complete_findings(findings: list[Finding], corrections: Corrections) -> list[Finding]:
    """One finding per catalog requirement, in catalog order. Unknown and duplicate ids are dropped."""
    by_id: dict[str, Finding] = {}
    for finding in findings:
        if finding.requirement_id in REQUIREMENT_IDS and finding.requirement_id not in by_id:
            by_id[finding.requirement_id] = finding.model_copy(deep=True)

    missing = [rid for rid in REQUIREMENT_IDS if rid not in by_id]
    for rid in missing:
        by_id[rid] = Finding(
            requirement_id=rid,
            status="needs_clarification",
            evidence=[],
            explanation="The AI assessment did not cover this requirement.",
            recommendation="Assess this requirement manually.",
        )
    if missing:
        corrections.add_note(f"The AI did not assess {', '.join(missing)}; marked for manual review.")

    return [by_id[rid] for rid in REQUIREMENT_IDS]


def verify_quotes(findings: list[Finding], scenario: str, corrections: Corrections) -> None:
    """Keep only quotes that appear verbatim in the scenario."""
    source = _normalize(scenario)
    removed = 0
    for finding in findings:
        verified: list[str] = []
        for quote in finding.evidence:
            cleaned = _clean_quote(quote)[:MAX_QUOTE_CHARS]
            if cleaned and _normalize(cleaned) in source and cleaned not in verified:
                verified.append(cleaned)
            else:
                removed += 1
        finding.evidence = verified[:MAX_QUOTES_PER_FINDING]
        corrections.quotes_verified += len(finding.evidence)

    corrections.quotes_removed += removed
    if removed:
        corrections.add_note(
            f"{removed} evidence quote(s) were removed because they do not appear in the scenario."
        )


def require_evidence_for_support(findings: list[Finding], corrections: Corrections) -> None:
    """A control cannot be rated supported unless the scenario shows it."""
    for finding in findings:
        if finding.status == "supported" and not finding.evidence:
            corrections.change_status(
                finding,
                "needs_clarification",
                f"{finding.requirement_id} was rated supported without evidence from the scenario; "
                "changed to needs clarification.",
            )


def _normalize(text: str) -> str:
    text = text.lower().translate(_QUOTE_FOLDING)
    return re.sub(r"\s+", " ", text).strip()


def _clean_quote(quote: str) -> str:
    return quote.strip().strip("\"'").strip().rstrip(".,;:").strip()

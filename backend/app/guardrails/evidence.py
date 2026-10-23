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
            explanation=corrections.text("missing.explanation"),
            recommendation=corrections.text("manual.action"),
        )
    if missing:
        corrections.add_note(corrections.text("missing.note", ids=", ".join(missing)))

    return [by_id[rid] for rid in REQUIREMENT_IDS]


def verify_quotes(findings: list[Finding], scenario: str, corrections: Corrections) -> None:
    """Keep only quotes that appear verbatim in the scenario."""
    source, positions = _indexed_normalize(scenario)
    removed = 0
    for finding in findings:
        verified: list[str] = []
        for quote in finding.evidence:
            cleaned = _clean_quote(quote)[:MAX_QUOTE_CHARS]
            normalized = _normalize(cleaned)
            start = source.find(normalized) if normalized else -1
            if start >= 0:
                # Match tolerantly, but return the original source characters unchanged.
                original = scenario[positions[start][0] : positions[start + len(normalized) - 1][1]]
                if original not in verified:
                    verified.append(original)
            else:
                removed += 1
        finding.evidence = verified[:MAX_QUOTES_PER_FINDING]
        corrections.quotes_verified += len(finding.evidence)

    corrections.quotes_removed += removed
    if removed:
        corrections.add_note(corrections.text("quotes.removed", count=removed))


def require_evidence_for_support(findings: list[Finding], corrections: Corrections) -> None:
    """A control cannot be rated supported unless the scenario shows it."""
    for finding in findings:
        if finding.status == "supported" and not finding.evidence:
            corrections.change_status(
                finding,
                "needs_clarification",
                corrections.text("support.missing", id=finding.requirement_id),
            )


def _normalize(text: str) -> str:
    text = text.lower().translate(_QUOTE_FOLDING)
    return re.sub(r"\s+", " ", text).strip()


def _clean_quote(quote: str) -> str:
    return quote.strip().strip("\"'").strip().rstrip(".,;:").strip()


def _indexed_normalize(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Normalize for matching while retaining offsets into the exact source text."""
    chars: list[str] = []
    positions: list[tuple[int, int]] = []
    for index, char in enumerate(text):
        if char.isspace():
            if chars and chars[-1] == " ":
                positions[-1] = (positions[-1][0], index + 1)
            elif chars:
                chars.append(" ")
                positions.append((index, index + 1))
            continue
        for folded in char.translate(_QUOTE_FOLDING).lower():
            chars.append(folded)
            positions.append((index, index + 1))
    if chars and chars[-1] == " ":
        chars.pop()
        positions.pop()
    return "".join(chars), positions

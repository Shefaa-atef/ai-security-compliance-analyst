"""Guardrails applied to the scenario before it reaches the model.

1. Normalize: remove invisible control and format characters that can hide text.
2. Redact: replace secrets and personal identifiers with typed placeholders, so
   the assessor itself complies with AI-002.
3. Detect prompt injection: flag text that tries to instruct the assessor.
   Flagged input is still assessed as data. The flag is shown to the user and
   recorded in the audit log, and the output guardrails still apply.
"""

import re
import unicodedata
from dataclasses import dataclass, field

# Order matters: more specific patterns run first.
_REDACTIONS: tuple[tuple[str, re.Pattern], ...] = (
    (
        "PRIVATE_KEY",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    ),
    (
        "API_KEY",
        re.compile(
            r"\b(?:sk-[A-Za-z0-9_\-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}"
            r"|xox[baprs]-[A-Za-z0-9\-]{10,}|AIza[0-9A-Za-z_\-]{30,})\b"
        ),
    ),
    ("CREDENTIAL", re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_ ]?key)\b\s*[:=]\s*\S+")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")),
    ("CARD_NUMBER", re.compile(r"\b(?:\d[ \-]?){13,19}\b")),
    ("NATIONAL_ID", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Digit groups must be separated, so plain ticket or account numbers are not treated as phones.
    ("PHONE", re.compile(r"(?<!\w)(?:\+\d{1,3}[\s.\-]?)?\(?\d{2,4}\)?[\s.\-]\d{3,4}[\s.\-]\d{3,4}\b")),
)

_INJECTION_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(pattern, re.I)
    for pattern in (
        r"\b(ignore|disregard|forget|override)\b.{0,40}\b(instructions|rules|prompt|guidelines|requirements)\b",
        r"\b(system|developer)\s+(prompt|message|instructions)\b",
        r"\byou\s+are\s+now\b",
        r"\bact\s+as\b.{0,40}\b(admin|developer|unrestricted|jailbroken)\b",
        r"\b(mark|rate|set|label)\b.{0,40}\b(all|every)\b.{0,40}\b(supported|compliant|low risk)\b",
        r"\breveal\b.{0,30}\b(prompt|instructions|key|secret)\b",
        r"</?\s*(scenario|system|instructions)\s*>",
    )
)


@dataclass
class PreparedInput:
    text: str
    redactions: dict[str, int] = field(default_factory=dict)
    injection_signals: list[str] = field(default_factory=list)

    @property
    def notes(self) -> list[str]:
        """User-facing explanations of what the input guardrails did."""
        notes = []
        if self.redactions:
            kinds = ", ".join(
                f"{label.lower().replace('_', ' ')} ({count})"
                for label, count in sorted(self.redactions.items())
            )
            notes.append(f"Sensitive values were redacted before AI analysis: {kinds}.")
        if self.injection_signals:
            notes.append(
                "The scenario contains text that looks like instructions to the assessor. "
                "It was treated as scenario data only; review the result with extra care."
            )
        return notes


def prepare_input(raw: str) -> PreparedInput:
    text = _strip_invisible(raw.replace("\r\n", "\n")).strip()
    text, redactions = _redact(text)
    signals = [match.group(0) for pattern in _INJECTION_PATTERNS if (match := pattern.search(text))]
    return PreparedInput(text=text, redactions=redactions, injection_signals=signals)


def _strip_invisible(text: str) -> str:
    """Remove control and format characters (zero-width, bidi overrides), keeping newlines and tabs."""
    return "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch) not in ("Cc", "Cf"))


def _redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for label, pattern in _REDACTIONS:

        def replace(match: re.Match, label: str = label) -> str:
            if label == "CARD_NUMBER" and not _luhn_valid(re.sub(r"\D", "", match.group(0))):
                return match.group(0)  # a long number that is not a card, such as a ticket id
            counts[label] = counts.get(label, 0) + 1
            return f"[REDACTED_{label}]"

        text = pattern.sub(replace, text)
    return text, counts


def _luhn_valid(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for index, char in enumerate(digits):
        digit = int(char)
        if index % 2 == parity:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0

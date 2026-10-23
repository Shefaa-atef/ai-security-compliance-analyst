"""Guardrails applied to user input before it reaches the model.

1. Normalize: remove control and zero-width characters that can hide text.
2. Redact: replace secrets and personal identifiers with typed placeholders,
   so the assessor itself complies with AI-002.
3. Detect prompt injection: flag text that tries to instruct the assessor.
   Flagged input is still assessed as data; the flag is surfaced to the user
   and recorded in the audit log, and output guardrails still apply.
"""
import re
from dataclasses import dataclass, field

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁠-⁤﻿]")

# Order matters: more specific patterns run first.
_REDACTIONS: tuple[tuple[str, re.Pattern], ...] = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
    ("API_KEY", re.compile(r"\b(?:sk-[A-Za-z0-9_\-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9\-]{10,})\b")),
    ("CREDENTIAL", re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_ ]?key)\b\s*[:=]\s*\S+")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")),
    ("CARD_NUMBER", re.compile(r"\b(?:\d[ \-]?){13,19}\b")),
    ("NATIONAL_ID", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Groups must be separated, so plain ticket or account numbers are not treated as phones.
    ("PHONE", re.compile(r"(?<!\w)(?:\+\d{1,3}[\s.\-]?)?\(?\d{2,4}\)?[\s.\-]\d{3,4}[\s.\-]\d{3,4}\b")),
)

_INJECTION_PATTERNS: tuple[re.Pattern, ...] = tuple(re.compile(p, re.I) for p in (
    r"\b(ignore|disregard|forget|override)\b.{0,40}\b(instructions|rules|prompt|guidelines|requirements)\b",
    r"\b(system|developer)\s+(prompt|message|instructions)\b",
    r"\byou\s+are\s+now\b",
    r"\bact\s+as\b.{0,40}\b(admin|developer|unrestricted|jailbroken)\b",
    r"\b(mark|rate|set|label)\b.{0,40}\b(all|every)\b.{0,40}\b(supported|compliant|low risk)\b",
    r"\breveal\b.{0,30}\b(prompt|instructions|key|secret)\b",
    r"</?\s*(scenario|system|instructions)\s*>",
))


@dataclass
class PreparedInput:
    text: str
    redactions: dict[str, int] = field(default_factory=dict)
    injection_signals: list[str] = field(default_factory=list)

    @property
    def notes(self) -> list[str]:
        notes = []
        if self.redactions:
            kinds = ", ".join(f"{k.lower().replace('_', ' ')} ({v})" for k, v in sorted(self.redactions.items()))
            notes.append(f"Sensitive values were redacted before AI analysis: {kinds}.")
        if self.injection_signals:
            notes.append("The scenario contains text that looks like instructions to the assessor. "
                         "It was treated as scenario data only; review the result with extra care.")
        return notes


def _luhn_valid(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def prepare_input(raw: str) -> PreparedInput:
    text = _CONTROL_CHARS.sub("", raw).replace("\r\n", "\n").strip()
    redactions: dict[str, int] = {}

    for label, pattern in _REDACTIONS:
        def _sub(match: re.Match, label=label) -> str:
            if label == "CARD_NUMBER":
                digits = re.sub(r"\D", "", match.group(0))
                if not _luhn_valid(digits):
                    return match.group(0)  # long number that is not a card, e.g. a ticket id
            redactions[label] = redactions.get(label, 0) + 1
            return f"[REDACTED_{label}]"
        text = pattern.sub(_sub, text)

    signals = [m.group(0) for p in _INJECTION_PATTERNS if (m := p.search(text))]
    return PreparedInput(text=text, redactions=redactions, injection_signals=signals)

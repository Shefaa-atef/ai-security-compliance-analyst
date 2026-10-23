"""Records every change the output guardrails make, so each one can be shown to the user."""

from dataclasses import dataclass, field

from ..i18n import ResponseLanguage, text
from ..schemas import Finding, Status


@dataclass
class Corrections:
    language: ResponseLanguage = "en"
    notes: list[str] = field(default_factory=list)
    quotes_verified: int = 0
    quotes_removed: int = 0
    status_changes: int = 0

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def change_status(self, finding: Finding, status: Status, reason: str) -> None:
        finding.status = status
        # A changed status must not retain a contradictory model explanation.
        finding.explanation = reason
        finding.recommendation = self.text("corrected.action")
        self.status_changes += 1
        self.notes.append(reason)

    def text(self, key: str, **values) -> str:
        return text(self.language, key, **values)

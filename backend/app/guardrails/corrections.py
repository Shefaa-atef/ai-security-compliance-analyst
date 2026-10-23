"""Records every change the output guardrails make, so each one can be shown to the user."""
from dataclasses import dataclass, field

from ..schemas import Finding, Status


@dataclass
class Corrections:
    notes: list[str] = field(default_factory=list)
    quotes_verified: int = 0
    quotes_removed: int = 0
    status_changes: int = 0

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def change_status(self, finding: Finding, status: Status, reason: str) -> None:
        finding.status = status
        self.status_changes += 1
        self.notes.append(reason)

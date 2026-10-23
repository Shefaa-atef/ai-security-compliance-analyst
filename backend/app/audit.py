"""Append-only audit log (JSON Lines).

Records what happened for every assessment without storing the scenario text
itself: a SHA-256 hash lets an auditor match a log entry to a submission while
keeping potentially sensitive content out of the logs.
"""

import hashlib
import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)
_lock = threading.Lock()


def scenario_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(path: str, event: dict) -> None:
    entry = {"timestamp": datetime.now(UTC).isoformat(), **event}
    try:
        file = Path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        with _lock, file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        # Audit failures must be visible to operators but must not leak to users.
        log.exception("Failed to write audit log entry")

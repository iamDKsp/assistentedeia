"""Utilities for persisting WhatsApp conversations."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


@dataclass(slots=True)
class MessageEntry:
    """Serializable representation of a message exchanged with a contact."""

    contact: str
    message: str
    direction: str  # "in" or "out"
    timestamp: datetime

    def as_serialisable(self) -> dict:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class ConversationLogger:
    """Append-only logger that stores messages as line delimited JSON."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: MessageEntry) -> None:
        with self.output_path.open("a", encoding="utf8") as stream:
            json.dump(entry.as_serialisable(), stream, ensure_ascii=False)
            stream.write("\n")

    def extend(self, entries: Iterable[MessageEntry]) -> None:
        for entry in entries:
            self.append(entry)

    def read(self) -> List[dict]:
        if not self.output_path.exists():
            return []
        with self.output_path.open("r", encoding="utf8") as stream:
            return [json.loads(line) for line in stream if line.strip()]


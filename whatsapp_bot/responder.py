"""Keyword based automatic response engine."""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Optional

from .config import ReplyConfig


@dataclass(slots=True)
class ReplyDecision:
    """Result of evaluating an incoming message."""

    message: str
    match: Optional[str]
    category: str


class KeywordResponder:
    """Selects appropriate replies based on keywords and commands."""

    def __init__(self, config: ReplyConfig) -> None:
        self.config = config

    def _normalise(self, text: str) -> str:
        return text.strip().lower()

    def evaluate(self, message: str) -> ReplyDecision:
        normalised = self._normalise(message)

        for command, response in self.config.command_replies.items():
            if normalised.startswith(command.lower()):
                return ReplyDecision(response, command, "command")

        for keyword, response in self.config.faq_replies.items():
            pattern = re.compile(rf"\b{re.escape(keyword.lower())}\b")
            if pattern.search(normalised):
                return ReplyDecision(response, keyword, "faq")

        return ReplyDecision(self.config.default_reply, None, "default")

    def random_delay(self) -> float:
        return random.uniform(*self.config.delay_range)


"""Application configuration models for the WhatsApp automation bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _normalise_delay(delay: Iterable[float]) -> List[float]:
    values = list(delay)
    if len(values) != 2:
        raise ValueError("Delay interval must contain exactly two values (min, max).")
    start, end = values
    if start < 0 or end < 0:
        raise ValueError("Delay interval must be positive numbers.")
    if start > end:
        raise ValueError("Delay interval start must be less than or equal to end.")
    return [float(start), float(end)]


@dataclass(slots=True)
class ReplyConfig:
    """Configuration for automated replies.

    Attributes
    ----------
    default_reply:
        Generic message sent when no keyword matches.
    faq_replies:
        Map of frequently asked questions keywords to responses.
    command_replies:
        Map of command keywords to responses (e.g. ``/help``).
    delay_range:
        A pair ``(min_seconds, max_seconds)`` controlling artificial typing delay.
    """

    default_reply: str = "Olá! Como posso ajudar?"
    faq_replies: Dict[str, str] = field(default_factory=dict)
    command_replies: Dict[str, str] = field(default_factory=dict)
    delay_range: List[float] = field(default_factory=lambda: [1.0, 3.0])

    def __post_init__(self) -> None:
        self.delay_range = _normalise_delay(self.delay_range)


@dataclass(slots=True)
class BotConfig:
    """Configuration container for :class:`~whatsapp_bot.bot.WhatsAppBot`."""

    session_dir: Path = Path(".whatsapp-session")
    headless: bool = False
    implicit_wait: float = 2.0
    reply: ReplyConfig = field(default_factory=ReplyConfig)
    qr_output: Optional[Path] = Path("qr_code.png")
    conversation_log: Path = Path("logs/conversations.log")


def build_config(
    *,
    default_reply: str = "Olá! Como posso ajudar?",
    faq_replies: Optional[Dict[str, str]] = None,
    command_replies: Optional[Dict[str, str]] = None,
    delay_range: Iterable[float] = (1, 3),
    session_dir: Optional[Path] = None,
    headless: bool = False,
    implicit_wait: float = 2.0,
    qr_output: Optional[Path] = Path("qr_code.png"),
    conversation_log: Path = Path("logs/conversations.log"),
) -> BotConfig:
    """Utility factory to create a :class:`BotConfig` from primitives.

    Parameters
    ----------
    default_reply:
        Generic fallback reply.
    faq_replies, command_replies:
        Keyword/command dictionaries.
    delay_range:
        Delay interval.
    session_dir:
        Path where the browser profile is stored. Persisting this folder
        allows the bot to reuse sessions and avoid logging in each time.
    headless:
        Whether to run the automation in headless mode.
    implicit_wait:
        Selenium implicit wait (in seconds).
    qr_output:
        Optional path where QR images should be stored. ``None`` disables the
        behaviour.
    conversation_log:
        File used to persist processed messages.
    """

    reply_cfg = ReplyConfig(
        default_reply=default_reply,
        faq_replies=faq_replies or {},
        command_replies=command_replies or {},
        delay_range=delay_range,
    )
    return BotConfig(
        session_dir=session_dir or BotConfig.session_dir,
        headless=headless,
        implicit_wait=implicit_wait,
        reply=reply_cfg,
        qr_output=qr_output,
        conversation_log=conversation_log,
    )

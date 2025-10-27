"""Command line entry point for running the WhatsApp automation bot."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from whatsapp_bot.bot import WhatsAppBot
from whatsapp_bot.config import BotConfig, build_config


def _load_mapping(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file '{path}' does not exist.")
    raw_text = path.read_text(encoding="utf8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        if not yaml:
            raise RuntimeError("PyYAML is required to read YAML configuration files.")
        data = yaml.safe_load(raw_text) or {}
    else:
        data = json.loads(raw_text or "{}")
    if not isinstance(data, dict):
        raise TypeError("Configuration must be a mapping of keys para valores.")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WhatsApp Web automation bot")
    parser.add_argument("config", type=Path, help="Path to the bot configuration file (JSON or YAML)")
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
    parser.add_argument("--poll", type=float, default=5.0, help="Polling interval in seconds")
    return parser.parse_args()


def build_bot_config(raw: Dict[str, Any], *, headless: bool) -> BotConfig:
    reply_cfg = raw.get("reply", {})
    return build_config(
        default_reply=reply_cfg.get("default", "Olá! Como posso ajudar?"),
        faq_replies=reply_cfg.get("faq", {}),
        command_replies=reply_cfg.get("commands", {}),
        delay_range=reply_cfg.get("delay", (1, 3)),
        session_dir=Path(raw.get("session_dir", ".whatsapp-session")),
        headless=headless or raw.get("headless", False),
        implicit_wait=float(raw.get("implicit_wait", 2.0)),
        qr_output=Path(raw.get("qr_output", "qr_code.png")) if raw.get("qr_output", True) else None,
        conversation_log=Path(raw.get("conversation_log", "logs/conversations.log")),
    )


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    raw_config = _load_mapping(args.config)
    config = build_bot_config(raw_config, headless=args.headless)
    bot = WhatsAppBot(config)
    bot.login()
    bot.run(poll_interval=args.poll)


if __name__ == "__main__":
    main()


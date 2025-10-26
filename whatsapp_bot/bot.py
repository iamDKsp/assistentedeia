"""High level WhatsApp Web automation robot."""
from __future__ import annotations

import logging
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import BrowserFactory
from .config import BotConfig
from .logger import ConversationLogger, MessageEntry
from .responder import KeywordResponder

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class IncomingMessage:
    contact: str
    text: str
    timestamp: datetime


class WhatsAppBot:
    """Encapsulates the automation required to interact with WhatsApp Web."""

    WHATSAPP_URL = "https://web.whatsapp.com/"

    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.browser_factory = BrowserFactory(config.session_dir, headless=config.headless)
        self.driver: Chrome = self.browser_factory.create()
        self.driver.implicitly_wait(config.implicit_wait)
        self.wait = WebDriverWait(self.driver, 30)
        self.responder = KeywordResponder(config.reply)
        self.logger = ConversationLogger(config.conversation_log)
        LOGGER.debug("Bot initialised with config: %s", config)

    # ------------------------------------------------------------------
    # Login helpers
    # ------------------------------------------------------------------
    def login(self, *, capture_qr: bool = True, timeout: int = 60) -> None:
        """Open WhatsApp Web and perform the login sequence.

        Parameters
        ----------
        capture_qr:
            When ``True`` the QR code is persisted to :class:`BotConfig.qr_output`.
        timeout:
            Maximum time (seconds) to wait for the interface to become ready.
        """

        LOGGER.info("Opening WhatsApp Web")
        self.driver.get(self.WHATSAPP_URL)

        if capture_qr and self.config.qr_output:
            with suppress(TimeoutException):
                self._capture_qr_code(timeout)

        LOGGER.info("Waiting for WhatsApp Web session to be ready")
        self._wait_until_logged_in(timeout)
        LOGGER.info("Successfully logged in to WhatsApp Web")

    def _capture_qr_code(self, timeout: int) -> None:
        LOGGER.debug("Capturing QR code")
        canvas = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
        )
        if not canvas:
            return
        png_bytes = canvas.screenshot_as_png
        output_path = self.config.qr_output
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(png_bytes)
            LOGGER.info("QR code saved to %s", output_path)

    def _wait_until_logged_in(self, timeout: int) -> None:
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='textbox'][contenteditable='true']")
            )
        )

    # ------------------------------------------------------------------
    # Chat helpers
    # ------------------------------------------------------------------
    def _unread_chat_elements(self) -> List[WebElement]:
        unread_badges = self.driver.find_elements(By.CSS_SELECTOR, "span[data-testid='icon-unread-count']")
        chats = []
        for badge in unread_badges:
            with suppress(NoSuchElementException):
                chat = badge.find_element(By.XPATH, "./ancestor::div[@data-testid='cell-frame-container']")
                chats.append(chat)
        return chats

    def _open_chat(self, element: WebElement) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()

    def _chat_header_contact(self) -> Optional[str]:
        try:
            header = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "header span[data-testid='conversation-info-header-contact-name']"))
            )
            contact = header.get_attribute("title") or header.text
            return contact.strip()
        except TimeoutException:
            return None

    def _chat_messages(self) -> List[WebElement]:
        container = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='conversation-panel-messages']"))
        )
        return container.find_elements(By.CSS_SELECTOR, "div[data-testid='msg-container']")

    def _extract_message(self, element: WebElement) -> Optional[str]:
        try:
            text_element = element.find_element(By.CSS_SELECTOR, "div.copyable-text")
            return text_element.text.strip()
        except NoSuchElementException:
            return None

    def _is_incoming(self, element: WebElement) -> bool:
        classes = element.get_attribute("class") or ""
        return "message-in" in classes

    def _send_reply(self, message: str) -> None:
        input_box = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "footer div[contenteditable='true'][data-tab='10']")
            )
        )
        input_box.click()
        input_box.send_keys(message)
        input_box.send_keys(Keys.ENTER)

    def _latest_incoming_message(self) -> Optional[IncomingMessage]:
        for element in reversed(self._chat_messages()):
            if not self._is_incoming(element):
                continue
            message = self._extract_message(element)
            if not message:
                continue
            timestamp_text = element.get_attribute("data-pre-plain-text") or ""
            timestamp = datetime.utcnow()
            return IncomingMessage(
                contact=self._chat_header_contact() or "Contato Desconhecido",
                text=message,
                timestamp=timestamp,
            )
        return None

    def _handle_chat(self, chat_element: WebElement) -> None:
        self._open_chat(chat_element)
        incoming = self._latest_incoming_message()
        if not incoming:
            LOGGER.debug("No incoming message detected for open chat")
            return
        LOGGER.info("Incoming message from %s: %s", incoming.contact, incoming.text)
        decision = self.responder.evaluate(incoming.text)
        LOGGER.info("Replying using %s rule", decision.category)
        time.sleep(self.responder.random_delay())
        self._send_reply(decision.message)
        now = datetime.utcnow()
        self.logger.extend(
            [
                MessageEntry(
                    contact=incoming.contact,
                    message=incoming.text,
                    direction="in",
                    timestamp=incoming.timestamp,
                ),
                MessageEntry(
                    contact=incoming.contact,
                    message=decision.message,
                    direction="out",
                    timestamp=now,
                ),
            ]
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_unread_chats(self) -> int:
        """Process all chats containing unread messages.

        Returns the number of chats handled.
        """

        chats = self._unread_chat_elements()
        if not chats:
            return 0
        for chat in chats:
            with suppress(Exception):
                self._handle_chat(chat)
        return len(chats)

    def run(self, poll_interval: float = 5.0) -> None:
        """Continuously monitor for incoming messages and respond automatically."""

        LOGGER.info("Starting monitoring loop")
        try:
            while True:
                processed = self.process_unread_chats()
                if processed:
                    LOGGER.debug("Processed %s chats", processed)
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            LOGGER.info("Stopping bot due to keyboard interrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        LOGGER.info("Closing browser session")
        with suppress(Exception):
            self.driver.quit()


"""Browser driver utilities for WhatsApp Web automation."""
from __future__ import annotations

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class BrowserFactory:
    """Create Selenium Chrome drivers with persistent sessions."""

    def __init__(self, session_dir: Path, headless: bool = False) -> None:
        self.session_dir = session_dir
        self.headless = headless
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument(f"--user-data-dir={self.session_dir.absolute()}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if self.headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver


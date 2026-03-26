"""E2E test fixtures for Playwright - manual browser management."""

import pytest
from playwright.sync_api import sync_playwright, Browser


@pytest.fixture(scope="session")
def browser():
    """Create a session-scoped browser instance."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    yield browser
    browser.close()
    pw.stop()


@pytest.fixture(scope="function")
def page(browser):
    """Create a function-scoped page for test isolation."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://localhost:5000"

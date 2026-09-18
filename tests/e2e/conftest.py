"""E2E test fixtures for Playwright - session-scoped page."""

import pytest
import os
from playwright.sync_api import sync_playwright, Browser


@pytest.fixture(scope="session")
def browser():
    """Create a session-scoped browser instance with CORS disabled."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    yield browser
    browser.close()
    pw.stop()


@pytest.fixture(scope="session")
def context(browser):
    """Create a session-scoped context."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture(scope="session")
def page(context):
    """Create a session-scoped page shared across all tests."""
    page = context.new_page()
    yield page


@pytest.fixture(scope="function")
def cleanup_page(page):
    """Reset page state between tests."""
    yield
    try:
        page.evaluate("() => { localStorage.clear(); }")
    except Exception:
        pass


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://localhost:5000"


@pytest.fixture(scope="session")
def widget_file_path():
    """Get the absolute path to widget HTML file."""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "desktop",
            "renderer",
            "index.html",
        )
    )


@pytest.fixture(scope="session")
def widget_url(widget_file_path):
    """Get file:// URL for widget HTML."""
    return f"file://{widget_file_path}"

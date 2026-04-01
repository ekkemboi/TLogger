"""E2E tests for price validation in desktop widget.

Tests validation guardrails for:
- LONG trades: TP must be > entry, SL must be < entry
- SHORT trades: TP must be < entry, SL must be > entry
"""

import pytest
import time
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def widget_base_url():
    """Base URL for the widget."""
    return "http://localhost:5000"


@pytest.fixture
def load_widget(page: Page, widget_base_url):
    """Load the widget page and expand Trade Info section."""
    page.goto(f"{widget_base_url}/trades", timeout=15000)
    page.wait_for_timeout(1000)

    # Expand Trade Info section if collapsed
    collapsible = page.locator(".collapsible-header, #trade-info-section").first
    if collapsible.is_visible():
        try:
            collapsible.click()
            page.wait_for_timeout(500)
        except:
            pass

    return page


def select_account_and_symbol(page: Page):
    """Helper to select account and symbol for testing."""
    # Select first available account
    account_select = page.locator("#account-select")
    if account_select.is_visible():
        account_select.select_option(index=1)  # Skip default option

    # Select first available symbol
    symbol_select = page.locator("#symbol-select")
    if symbol_select.is_visible():
        symbol_select.select_option(index=1)  # Skip default option

    page.wait_for_timeout(300)


class TestLongTradeWidgetValidation:
    """Tests for LONG trade price validation in widget."""

    def test_long_tp_less_than_entry_shows_error(self, page: Page, widget_base_url):
        """LONG trade with TP < entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP less than entry (invalid)
        page.locator("#take-profit").fill("49000")

        # Fill SL less than entry (valid)
        page.locator("#stop-loss").fill("49000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text or "take_profit" in text or "greater" in text
        print(f"✅ LONG TP < entry validation error shown: {text}")

    def test_long_sl_greater_than_entry_shows_error(self, page: Page, widget_base_url):
        """LONG trade with SL > entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP greater than entry (valid)
        page.locator("#take-profit").fill("51000")

        # Fill SL greater than entry (invalid)
        page.locator("#stop-loss").fill("51000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text or "stop_loss" in text or "less" in text
        print(f"✅ LONG SL > entry validation error shown: {text}")

    def test_long_valid_prices_succeed(self, page: Page, widget_base_url):
        """LONG trade with valid TP > entry AND SL < entry should succeed."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill valid TP > entry
        page.locator("#take-profit").fill("51000")

        # Fill valid SL < entry
        page.locator("#stop-loss").fill("49000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text
        print(f"✅ LONG with valid prices succeeded: {text}")

    def test_long_tp_equal_to_entry_shows_error(self, page: Page, widget_base_url):
        """LONG trade with TP = entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP equal to entry (invalid - must be greater)
        page.locator("#take-profit").fill("50000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text
        print(f"✅ LONG TP = entry validation error shown: {text}")


class TestShortTradeWidgetValidation:
    """Tests for SHORT trade price validation in widget."""

    def test_short_tp_greater_than_entry_shows_error(self, page: Page, widget_base_url):
        """SHORT trade with TP > entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP greater than entry (invalid)
        page.locator("#take-profit").fill("51000")

        # Fill SL less than entry (valid for SHORT)
        page.locator("#stop-loss").fill("49000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text or "take_profit" in text or "less" in text
        print(f"✅ SHORT TP > entry validation error shown: {text}")

    def test_short_sl_less_than_entry_shows_error(self, page: Page, widget_base_url):
        """SHORT trade with SL < entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP less than entry (valid for SHORT)
        page.locator("#take-profit").fill("49000")

        # Fill SL less than entry (invalid)
        page.locator("#stop-loss").fill("49000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text or "stop_loss" in text or "greater" in text
        print(f"✅ SHORT SL < entry validation error shown: {text}")

    def test_short_valid_prices_succeed(self, page: Page, widget_base_url):
        """SHORT trade with valid TP < entry AND SL > entry should succeed."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill valid TP < entry
        page.locator("#take-profit").fill("49000")

        # Fill valid SL > entry
        page.locator("#stop-loss").fill("51000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text
        print(f"✅ SHORT with valid prices succeeded: {text}")

    def test_short_tp_equal_to_entry_shows_error(self, page: Page, widget_base_url):
        """SHORT trade with TP = entry should show validation error."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Fill TP equal to entry (invalid - must be less)
        page.locator("#take-profit").fill("50000")

        # Fill position size
        page.locator("#position-size").fill("1")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for error
        page.wait_for_timeout(1000)

        # Check for error message
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "error" in text
        print(f"✅ SHORT TP = entry validation error shown: {text}")


class TestOptionalFieldsWidgetValidation:
    """Tests for optional TP/SL fields in widget."""

    def test_long_missing_tp_allowed(self, page: Page, widget_base_url):
        """LONG trade without TP should be allowed (optional field)."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form without TP
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Only fill SL (valid for LONG)
        page.locator("#stop-loss").fill("49000")

        # Leave TP empty (optional)

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message (TP is optional)
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text or "trade" in text
        print(f"✅ LONG without TP succeeded (optional field): {text}")

    def test_long_missing_sl_allowed(self, page: Page, widget_base_url):
        """LONG trade without SL should be allowed (optional field)."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form without SL
        select_account_and_symbol(page)

        # Set direction to LONG
        page.locator("#direction").select_option("long")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Only fill TP (valid for LONG)
        page.locator("#take-profit").fill("51000")

        # Leave SL empty (optional)

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message (SL is optional)
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text or "trade" in text
        print(f"✅ LONG without SL succeeded (optional field): {text}")

    def test_short_missing_tp_allowed(self, page: Page, widget_base_url):
        """SHORT trade without TP should be allowed (optional field)."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form without TP
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Only fill SL (valid for SHORT)
        page.locator("#stop-loss").fill("51000")

        # Leave TP empty (optional)

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message (TP is optional)
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text or "trade" in text
        print(f"✅ SHORT without TP succeeded (optional field): {text}")

    def test_short_missing_sl_allowed(self, page: Page, widget_base_url):
        """SHORT trade without SL should be allowed (optional field)."""
        page.goto(f"{widget_base_url}/trades", timeout=15000)
        page.wait_for_timeout(1000)

        # Expand Trade Info section
        collapsible = page.locator(".collapsible-header").first
        if collapsible.is_visible():
            collapsible.click()
            page.wait_for_timeout(500)

        # Fill form without SL
        select_account_and_symbol(page)

        # Set direction to SHORT
        page.locator("#direction").select_option("short")

        # Fill entry price
        page.locator("#entry-price").fill("50000")

        # Only fill TP (valid for SHORT)
        page.locator("#take-profit").fill("49000")

        # Leave SL empty (optional)

        # Fill position size
        page.locator("#position-size").fill("1")

        # Set outcome
        page.locator("#outcome").select_option("win")

        # Submit
        page.locator("#confirm-btn").click()

        # Wait for response
        page.wait_for_timeout(2000)

        # Check for success message (SL is optional)
        status = page.locator("#status-message")
        assert status.is_visible()
        text = status.text_content().lower()
        assert "success" in text or "saved" in text or "pnl" in text or "trade" in text
        print(f"✅ SHORT without SL succeeded (optional field): {text}")

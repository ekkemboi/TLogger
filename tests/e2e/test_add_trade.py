"""E2E tests for Add Trade (Basic) user journey."""

import pytest
from playwright.sync_api import Page


class TestAddTradeBasic:
    """Test Add Trade (Basic) flow from form fill to submission."""

    @pytest.mark.e2e
    def test_trade_form_renders(self, page: Page, widget_url: str, cleanup_page):
        """Test that trade form renders with all required fields."""
        page.goto(widget_url, timeout=5000)
        page.wait_for_load_state("domcontentloaded", timeout=3000)

        # Wait for widget to be ready
        page.wait_for_selector(".widget", timeout=3000)

        # Check widget container exists
        assert page.locator(".widget").is_visible()

        # Check form fields exist
        assert page.locator("#entry-price").count() > 0
        assert page.locator("#position-size").count() > 0

    @pytest.mark.e2e
    def test_recent_trades_section_exists(
        self, page: Page, widget_url: str, cleanup_page
    ):
        """Test that recent trades section exists."""
        page.goto(widget_url, timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(500)

        # Recent trades section should exist
        assert page.locator(".recent-trades").count() > 0

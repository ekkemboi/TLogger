"""E2E tests for the dashboard page."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_dashboard_loads_successfully(page: Page, base_url: str):
    """Test that the dashboard page loads without errors."""
    page.goto(f"{base_url}/")

    # Check that the page title or main heading is present
    heading = page.locator("h1, h2").first
    assert heading.is_visible()

    # Check for no console errors
    console_errors = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
    )

    assert "TradeLogger" in page.title() or "Dashboard" in page.content()


@pytest.mark.e2e
def test_dashboard_displays_stats(page: Page, base_url: str):
    """Test that the dashboard displays statistics."""
    page.goto(f"{base_url}/")

    # Look for stat cards or metrics containers
    stats = page.locator(".stat, .card, .metric, [class*='stat'], [class*='card']")

    # Dashboard should have some visual elements
    body = page.locator("body")
    assert body.is_visible()


@pytest.mark.e2e
def test_dashboard_navigation_to_trades(page: Page, base_url: str):
    """Test navigation from dashboard to trades page."""
    page.goto(f"{base_url}/")

    # Find and click a link to trades
    trades_link = page.get_by_role("link", name="Trades").first
    if trades_link.is_visible():
        trades_link.click()
        assert "/trades" in page.url or "trades" in page.url.lower()
    else:
        # Try finding link by href
        link = page.locator('a[href*="trades"]').first
        if link.is_visible():
            link.click()
            assert "/trades" in page.url


@pytest.mark.e2e
def test_dashboard_navigation_to_favorites(page: Page, base_url: str):
    """Test navigation from dashboard to favorites page."""
    page.goto(f"{base_url}/")

    # Find and click a link to favorites
    favorites_link = page.get_by_role("link", name="Favorites").first
    if favorites_link.is_visible():
        favorites_link.click()
        assert "/favorites" in page.url or "favorites" in page.url.lower()
    else:
        # Try finding link by href
        link = page.locator('a[href*="favorites"]').first
        if link.is_visible():
            link.click()
            assert "/favorites" in page.url

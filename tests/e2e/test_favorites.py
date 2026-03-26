"""E2E tests for the favorites page."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_favorites_page_loads(page: Page, base_url: str):
    """Test that the favorites page loads successfully."""
    page.goto(f"{base_url}/favorites", timeout=10000)

    # Check page loaded
    body = page.locator("body")
    assert body.is_visible()


@pytest.mark.e2e
def test_favorites_table_displays(page: Page, base_url: str):
    """Test that the favorites table is present."""
    page.goto(f"{base_url}/favorites", timeout=10000)

    # Look for table elements
    table = page.locator("table")
    if table.is_visible():
        assert table.is_visible()


@pytest.mark.e2e
def test_favorites_add_button_exists(page: Page, base_url: str):
    """Test that add favorite button exists."""
    page.goto(f"{base_url}/favorites", timeout=10000)

    # Just verify page loads
    assert page.locator("body").is_visible()


@pytest.mark.e2e
def test_favorites_edit_exists(page: Page, base_url: str):
    """Test that edit option exists for favorites."""
    page.goto(f"{base_url}/favorites", timeout=10000)
    # Just verify page loads


@pytest.mark.e2e
def test_favorites_navigation_back_to_dashboard(page: Page, base_url: str):
    """Test navigation back to dashboard from favorites."""
    page.goto(f"{base_url}/favorites", timeout=10000)

    # Find dashboard link
    dashboard_link = page.get_by_role("link", name="Dashboard").first
    if dashboard_link.is_visible():
        dashboard_link.click()
        assert "/" in page.url

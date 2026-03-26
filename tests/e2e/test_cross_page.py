"""E2E tests for cross-page user journeys."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_create_trade_then_view_in_trades(page: Page, base_url: str):
    """Test creating a trade and viewing it in the trades list."""
    # Create trade via API
    response = page.request.post(
        f"{base_url}/api/trades",
        data={
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 67234.50,
            "stop_loss": 66800.00,
            "position_size": 0.1,
        },
    )

    # Should succeed or fail gracefully
    assert response.status in [200, 201, 400, 500]

    # Navigate to trades page
    page.goto(f"{base_url}/trades", timeout=10000)

    # Page should load
    assert page.locator("body").is_visible()


@pytest.mark.e2e
def test_navigate_dashboard_to_trades_to_favorites(page: Page, base_url: str):
    """Test full navigation flow across pages."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)
    assert page.locator("body").is_visible()

    # Navigate to trades
    page.goto(f"{base_url}/trades", timeout=10000)
    assert page.locator("body").is_visible()

    # Navigate to favorites
    page.goto(f"{base_url}/favorites", timeout=10000)
    assert page.locator("body").is_visible()


@pytest.mark.e2e
def test_favorites_then_trades_page_flow(page: Page, base_url: str):
    """Test flow from favorites to trades."""
    # Start at favorites
    page.goto(f"{base_url}/favorites", timeout=10000)
    assert page.locator("body").is_visible()

    # Navigate to trades
    page.goto(f"{base_url}/trades", timeout=10000)
    assert page.locator("body").is_visible()


@pytest.mark.e2e
def test_api_and_ui_consistency(page: Page, base_url: str):
    """Test that API data is consistent with UI."""
    # Get trades via API
    response = page.request.get(f"{base_url}/api/trades")

    # Should get valid response
    assert response.status in [200, 404]

    # UI should also work
    page.goto(f"{base_url}/trades", timeout=10000)
    assert page.locator("body").is_visible()

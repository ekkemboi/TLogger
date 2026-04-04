"""E2E tests for HTMX sidebar navigation - v2 redesign."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_htmx_sidebar_navigation_no_duplication(page: Page, base_url: str):
    """Test that sidebar doesn't duplicate when navigating with HTMX."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)

    # Wait for page to load - sidebar is 260px wide with bg-secondary
    page.wait_for_selector("aside.sidebar", timeout=5000)

    # Count sidebars - should be exactly 1
    sidebar_count = page.locator("aside.sidebar").count()
    assert sidebar_count == 1, f"Expected 1 sidebar, found {sidebar_count}"

    # Click on Trades link (uses HTMX hx-get attributes)
    trades_link = page.locator("a[hx-get='/trades']")
    expect(trades_link).to_be_visible()
    trades_link.click()
    page.wait_for_timeout(800)  # Wait for HTMX swap

    # Count sidebars again - should still be 1 (not duplicated)
    sidebar_count = page.locator("aside.sidebar").count()
    assert sidebar_count == 1, (
        f"After navigation, expected 1 sidebar, found {sidebar_count}"
    )

    # Verify content loaded in main area (should have Trades heading)
    main_content = page.locator("main.main-content")
    expect(main_content).to_contain_text("Trades")


@pytest.mark.e2e
def test_htmx_navigation_content_visible(page: Page, base_url: str):
    """Test that content is visible (not blank) when navigating with HTMX."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_selector("aside.sidebar", timeout=5000)

    # Navigate to Accounts via HTMX
    accounts_link = page.locator("a[hx-get='/accounts']")
    expect(accounts_link).to_be_visible()
    accounts_link.click()
    page.wait_for_timeout(800)

    # Verify accounts content is visible (not blank) - look for h1 with Accounts
    main_content = page.locator("main.main-content")
    expect(main_content).to_contain_text("Accounts")

    # Navigate to Favorites via HTMX
    favorites_link = page.locator("a[hx-get='/favorites']")
    expect(favorites_link).to_be_visible()
    favorites_link.click()
    page.wait_for_timeout(800)

    # Verify favorites content is visible
    expect(main_content).to_contain_text("Favorites")

    # Navigate to Trades via HTMX
    trades_link = page.locator("a[hx-get='/trades']")
    expect(trades_link).to_be_visible()
    trades_link.click()
    page.wait_for_timeout(800)

    # Verify trades content is visible
    expect(main_content).to_contain_text("Trades")


@pytest.mark.e2e
def test_htmx_navigation_url_updates(page: Page, base_url: str):
    """Test that URL updates correctly with HTMX hx-push-url."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_selector("aside.sidebar", timeout=5000)

    # Click Trades (should update URL via hx-push-url)
    trades_link = page.locator("a[hx-get='/trades']")
    trades_link.click()
    page.wait_for_timeout(800)

    # URL should be /trades
    expect(page).to_have_url(f"{base_url}/trades")

    # Click Accounts
    accounts_link = page.locator("a[hx-get='/accounts']")
    accounts_link.click()
    page.wait_for_timeout(800)

    # URL should be /accounts
    expect(page).to_have_url(f"{base_url}/accounts")


@pytest.mark.e2e
def test_htmx_active_state_updates(page: Page, base_url: str):
    """Test that sidebar active state updates on HTMX navigation."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_selector("aside.sidebar", timeout=5000)

    # Dashboard should have 'active' class initially
    active_link = page.locator("nav a.active")
    expect(active_link).to_contain_text("Dashboard")

    # Navigate to Trades
    trades_link = page.locator("a[hx-get='/trades']")
    trades_link.click()
    page.wait_for_timeout(800)

    # After HTMX swap, Trades should have active class (updated by JS)
    # Note: Active state is set by htmx:afterSwap event handler
    active_link = page.locator("nav a.active")
    expect(active_link).to_contain_text("Trades")


@pytest.mark.e2e
def test_htmx_content_not_nested(page: Page, base_url: str):
    """Test that HTMX content doesn't get nested inside old content."""
    # Start at dashboard
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_selector("aside.sidebar", timeout=5000)

    # Get initial main content HTML
    main = page.locator("main.main-content")
    initial_html = main.inner_html()

    # Navigate to Trades
    trades_link = page.locator("a[hx-get='/trades']")
    trades_link.click()
    page.wait_for_timeout(800)

    # Get new main content HTML
    new_html = main.inner_html()

    # Content should have changed
    assert new_html != initial_html, "Content should have changed after navigation"

    # Should not contain nested main elements
    main_count = page.locator("main").count()
    assert main_count == 1, f"Should have exactly 1 main element, found {main_count}"

    # Should not contain nested sidebar
    sidebar_in_main = main.locator("aside.sidebar").count()
    assert sidebar_in_main == 0, "Sidebar should not be inside main content"

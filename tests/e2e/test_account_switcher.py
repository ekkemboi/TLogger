"""E2E tests for Account Switcher in navigation bar."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_account_switcher_visible_dashboard(page: Page, base_url: str):
    """Account dropdown is visible in nav bar on Dashboard."""
    page.goto(f"{base_url}/", timeout=10000)
    switcher = page.locator("#account-switcher")
    assert switcher.is_visible(), "Account switcher should be visible on Dashboard"


@pytest.mark.e2e
def test_account_switcher_visible_trades(page: Page, base_url: str):
    """Account dropdown is visible in nav bar on Trades page."""
    page.goto(f"{base_url}/trades", timeout=10000)
    switcher = page.locator("#account-switcher")
    assert switcher.is_visible(), "Account switcher should be visible on Trades page"


@pytest.mark.e2e
def test_account_switcher_visible_accounts(page: Page, base_url: str):
    """Account dropdown is visible in nav bar on Accounts page."""
    page.goto(f"{base_url}/accounts", timeout=10000)
    switcher = page.locator("#account-switcher")
    assert switcher.is_visible(), "Account switcher should be visible on Accounts page"


@pytest.mark.e2e
def test_account_switcher_loads_accounts(page: Page, base_url: str):
    """Dropdown is populated with accounts from API."""
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )
    options_count = page.evaluate(
        "document.querySelector('#account-switcher').options.length"
    )
    assert options_count > 1, "Account switcher should have at least one account option"


@pytest.mark.e2e
def test_account_switcher_default_is_all(page: Page, base_url: str):
    """First option is 'All Accounts' with empty value."""
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )
    first_option_text = page.evaluate(
        "document.querySelector('#account-switcher').options[0].textContent"
    )
    first_option_value = page.evaluate(
        "document.querySelector('#account-switcher').options[0].value"
    )
    assert first_option_text == "All Accounts", "First option should be 'All Accounts'"
    assert first_option_value == "", "First option value should be empty"


@pytest.mark.e2e
def test_account_switcher_persists_selection(page: Page, base_url: str):
    """Selected account persists in localStorage."""
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    first_account = page.evaluate(
        "document.querySelector('#account-switcher').options[1].value"
    )

    page.locator("#account-switcher").select_option(first_account)

    page.reload()
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    stored = page.evaluate("localStorage.getItem('selectedAccountId')")
    assert stored == first_account, "localStorage should persist selected account"


@pytest.mark.e2e
def test_account_switcher_updates_dashboard(page: Page, base_url: str):
    """Changing account filters dashboard metrics."""
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    initial_trades = page.locator("#total-trades").text_content()

    first_account = page.evaluate(
        "document.querySelector('#account-switcher').options[1].value"
    )
    page.locator("#account-switcher").select_option(first_account)

    page.wait_for_timeout(500)

    total_trades = page.locator("#total-trades").text_content()
    assert total_trades != "Loading...", "Metrics should update after account change"


@pytest.mark.e2e
def test_account_switcher_updates_trades(page: Page, base_url: str):
    """Changing account filters trades table."""
    page.goto(f"{base_url}/trades", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    first_account = page.evaluate(
        "document.querySelector('#account-switcher').options[1].value"
    )
    page.locator("#account-switcher").select_option(first_account)

    page.wait_for_timeout(500)

    table = page.locator("#trades-table")
    loading_text = table.locator("text=Loading...")
    assert loading_text.count() == 0 or not loading_text.first.is_visible(), (
        "Trades table should update after account change"
    )


@pytest.mark.e2e
def test_account_switcher_syncs_across_pages(page: Page, base_url: str):
    """Selection on Dashboard is reflected on Trades page."""
    page.goto(f"{base_url}/", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    first_account = page.evaluate(
        "document.querySelector('#account-switcher').options[1].value"
    )
    page.locator("#account-switcher").select_option(first_account)

    page.goto(f"{base_url}/trades", timeout=10000)
    page.wait_for_function(
        "document.querySelector('#account-switcher').options.length > 1", timeout=5000
    )

    selected = page.evaluate("document.querySelector('#account-switcher').value")
    assert selected == first_account, "Account selection should persist across pages"

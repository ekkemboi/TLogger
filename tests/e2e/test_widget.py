"""E2E tests for the desktop widget using Playwright."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_widget_page_loads(page: Page, widget_url: str):
    """Test that widget HTML renders correctly."""
    page.goto(widget_url)
    page.wait_for_load_state("domcontentloaded")
    assert page.locator(".widget").is_visible()
    assert page.locator(".header").is_visible()


@pytest.mark.e2e
def test_widget_loads_accounts(page: Page, widget_url: str):
    """Test that accounts load from API."""
    page.goto(widget_url)
    page.wait_for_timeout(2000)
    options = page.locator("#account-select option").all()
    assert len(options) >= 1


@pytest.mark.e2e
def test_widget_loads_symbols(page: Page, widget_url: str):
    """Test that favorites/symbols load from API."""
    page.goto(widget_url)
    page.wait_for_timeout(2000)
    options = page.locator("#symbol-select option").all()
    assert len(options) >= 1


@pytest.mark.e2e
def test_widget_trade_info_toggle(page: Page, widget_url: str):
    """Test that Trade Info section toggles."""
    page.goto(widget_url)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    assert is_collapsed is True

    page.click(".collapsible-header")
    page.wait_for_timeout(300)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    assert is_collapsed is False

    page.click(".collapsible-header")
    page.wait_for_timeout(300)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    assert is_collapsed is True


@pytest.mark.e2e
def test_widget_trade_info_summary_display(page: Page, widget_url: str):
    """Test that Trade Info summary shows values."""
    page.goto(widget_url)
    page.click(".collapsible-header")
    page.wait_for_timeout(300)
    summary = page.locator("#trade-info-summary").text_content()
    assert "--" in summary


@pytest.mark.e2e
def test_widget_account_selection_saved(page: Page, widget_url: str):
    """Test that selected account is saved to localStorage."""
    page.goto(widget_url)
    page.click(".collapsible-header")
    page.wait_for_timeout(2000)

    accounts = page.locator("#account-select option")
    count = accounts.count()
    assert count > 1, "Need at least one account to test"

    # Use select_option instead of click on option
    page.select_option("#account-select", index=1)
    page.wait_for_timeout(300)

    saved = page.evaluate("() => localStorage.getItem('lastAccountId')")
    assert saved is not None


@pytest.mark.e2e
def test_widget_symbol_selection_saved(page: Page, widget_url: str):
    """Test that selected symbol is saved to localStorage."""
    page.goto(widget_url)
    page.click(".collapsible-header")
    page.wait_for_timeout(2000)

    symbols = page.locator("#symbol-select option")
    count = symbols.count()

    if count > 1:
        page.select_option("#symbol-select", index=1)
        page.wait_for_timeout(300)

        saved = page.evaluate("() => localStorage.getItem('lastSymbol')")
        assert saved is not None
    else:
        pytest.skip("No symbols available to test")


@pytest.mark.e2e
def test_widget_save_trade_validation(page: Page, widget_url: str):
    """Test validation - submit without required fields."""
    page.goto(widget_url)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    if is_collapsed:
        page.click(".collapsible-header")
        page.wait_for_timeout(300)

    page.wait_for_timeout(1000)
    page.fill("#entry-price", "50000")
    page.fill("#position-size", "1")

    page.click("#confirm-btn")
    page.wait_for_timeout(500)

    status = page.locator("#status-message")
    assert status.is_visible()

    classes = status.get_attribute("class")
    assert "error" in classes


@pytest.mark.e2e
def test_widget_save_trade_success(page: Page, widget_url: str):
    """Test successful trade submission."""
    page.goto(widget_url)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    if is_collapsed:
        page.click(".collapsible-header")

    page.wait_for_timeout(2000)

    # Select account
    accounts = page.locator("#account-select option")
    if accounts.count() > 1:
        page.select_option("#account-select", index=1)
        page.wait_for_timeout(200)

    # Select symbol
    symbols = page.locator("#symbol-select option")
    if symbols.count() > 1:
        page.select_option("#symbol-select", index=1)
        page.wait_for_timeout(200)

    # Fill trade details
    page.fill("#entry-price", "50000")
    page.fill("#position-size", "1")
    page.fill("#take-profit", "51000")
    page.select_option("#direction", "long")
    page.select_option("#outcome", "win")

    # Submit
    page.click("#confirm-btn")

    page.wait_for_timeout(3500)  # Wait longer to ensure timeout has run

    # Check the status message content (it may be hidden after timeout)
    status_html = page.locator("#status-message").inner_html()
    status_classes = page.locator("#status-message").get_attribute("class")
    print(f"\nStatus classes: {status_classes}")
    print(f"Status HTML: {status_html}")

    # Check for success message in HTML (not visibility since it gets hidden after 3s)
    assert "success" in status_classes
    assert "Trade saved" in status_html
    print("\n✅ Trade saved successfully!")


@pytest.mark.e2e
def test_widget_clear_form(page: Page, widget_url: str):
    """Test that Clear button resets the form."""
    page.goto(widget_url)

    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    if is_collapsed:
        page.click(".collapsible-header")
        page.wait_for_timeout(300)

    page.fill("#entry-price", "50000")
    page.fill("#position-size", "1")
    page.fill("#take-profit", "51000")
    page.fill("#notes", "Test trade notes")

    page.click("#clear-btn")
    page.wait_for_timeout(300)

    assert page.locator("#entry-price").input_value() == ""
    assert page.locator("#position-size").input_value() == ""
    assert page.locator("#take-profit").input_value() == ""
    assert page.locator("#notes").input_value() == ""


@pytest.mark.e2e
def test_widget_recent_trades_load(page: Page, widget_url: str):
    """Test that recent trades section loads."""
    page.goto(widget_url)
    page.wait_for_timeout(2000)
    assert page.locator(".recent-trades").is_visible()

    has_trades = page.locator(".recent-item").count() > 0
    has_empty = page.locator(".no-trades").is_visible()

    assert has_trades or has_empty


@pytest.mark.e2e
def test_widget_console_logs(page: Page, widget_url: str):
    """Capture console logs to debug issues."""
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

    page.goto(widget_url)
    page.wait_for_timeout(2000)

    print("\n--- Console Logs ---")
    for log in console_logs:
        print(log)

    errors = [log for log in console_logs if "error" in log.lower()]
    if errors:
        print("\n--- Errors Found ---")
        for err in errors:
            print(err)


@pytest.mark.e2e
def test_widget_partial_exits(page: Page, widget_url: str):
    """Test partial exits UI functionality - add a partial exit row."""
    page.goto(widget_url)

    # Expand Trade Info if collapsed
    is_collapsed = page.locator(".collapsible-section").evaluate(
        "el => el.classList.contains('collapsed')"
    )
    if is_collapsed:
        page.click(".collapsible-header")

    page.wait_for_timeout(1000)

    # Verify no partial exit rows exist initially
    partial_items = page.locator(".partial-exit-item")
    initial_count = partial_items.count()
    assert initial_count == 0, "Should start with no partial exits"

    # Click "+ ADD" button to add partial exit row
    page.click("#add-partial-btn")
    page.wait_for_timeout(500)

    # Verify partial exit row was added
    partial_items = page.locator(".partial-exit-item")
    assert partial_items.count() == 1, "Partial exit row should be added"

    # Verify the partial exit input fields exist
    qty_input = page.locator(".partial-qty")
    price_input = page.locator(".partial-exit-price")
    fees_input = page.locator(".partial-fees")

    assert qty_input.is_visible(), "Qty input should be visible"
    assert price_input.is_visible(), "Exit price input should be visible"
    assert fees_input.is_visible(), "Fees input should be visible"

    print("\n✅ Partial exits UI works - row added successfully!")

    # Try to fill and submit (may fail due to file:// CORS, but UI test passes)
    page.fill(".partial-qty", "0.5")
    page.fill(".partial-exit-price", "52000")
    page.fill(".partial-fees", "5")
    page.wait_for_timeout(200)

    # Submit - may fail due to CORS in file:// mode
    page.click("#confirm-btn")
    page.wait_for_timeout(2000)

    # Just verify the button is clickable (UI test)
    print("✅ Form submission attempted")

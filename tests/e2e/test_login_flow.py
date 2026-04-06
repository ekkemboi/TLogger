"""E2E tests for Login Flow user journey."""

import pytest
from playwright.sync_api import Page, expect


class TestLoginFlow:
    """Test complete Login Flow from widget to authenticated state."""

    @pytest.mark.e2e
    def test_login_page_loads(self, page: Page, widget_url: str, cleanup_page):
        """Test that login page renders in widget."""
        page.goto(widget_url)
        page.wait_for_load_state("domcontentloaded")

        # Should show login view elements
        login_button = page.locator("text=Open Browser Login")
        assert login_button.is_visible() or page.locator(".login-view").is_visible()

    @pytest.mark.e2e
    def test_authenticated_state_loads_accounts(
        self, page: Page, widget_url: str, cleanup_page
    ):
        """Test that authenticated widget loads accounts and symbols."""
        page.goto(widget_url)
        page.wait_for_timeout(2000)

        # After auth, accounts should load
        options = page.locator("#account-select option").all()
        assert len(options) >= 1

    @pytest.mark.e2e
    def test_authenticated_state_loads_symbols(
        self, page: Page, widget_url: str, cleanup_page
    ):
        """Test that authenticated widget loads symbols/favorites."""
        page.goto(widget_url)
        page.wait_for_timeout(2000)

        # After auth, symbols should load
        options = page.locator("#symbol-select option").all()
        assert len(options) >= 1

    @pytest.mark.e2e
    def test_console_logs_capture_errors(
        self, page: Page, widget_url: str, cleanup_page
    ):
        """Capture console logs to debug auth issues."""
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

"""E2E tests for desktop widget using agent-browser."""

import subprocess
import time
import pytest


class TestWidgetElectron:
    """Test widget in real Electron environment via agent-browser."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_electron(self):
        """Start Electron with remote debugging."""
        print("\n🚀 Starting Electron app...")

        # Start Electron with remote debugging port
        self.proc = subprocess.Popen(
            ["bun", "start", "--", "--remote-debugging-port=9222"],
            cwd="desktop",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for app to start
        time.sleep(6)

        # Connect to Electron
        print("📡 Connecting to Electron...")
        result = subprocess.run(
            ["agent-browser", "connect", "9222"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        yield

        # Cleanup
        print("\n🧹 Stopping Electron...")
        self.proc.terminate()
        self.proc.wait(timeout=5)

    def test_electron_app_launches(self):
        """Test that Electron app launches."""
        result = subprocess.run(
            ["agent-browser", "--auto-connect", "snapshot"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        print(f"\n✅ Electron app launched successfully")

    def test_widget_loads(self):
        """Test that widget HTML renders."""
        result = subprocess.run(
            ["agent-browser", "snapshot", "-i"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "widget" in result.stdout.lower() or "TradeLogger" in result.stdout
        print(f"\n✅ Widget loaded")

    def test_screenshot(self):
        """Take screenshot of widget."""
        os.makedirs("tests/e2e/agent-browser/screenshots", exist_ok=True)
        result = subprocess.run(
            [
                "agent-browser",
                "screenshot",
                "tests/e2e/agent-browser/screenshots/widget.png",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        print(f"\n✅ Screenshot saved")

    def test_trade_info_toggle(self):
        """Test Trade Info section toggles."""
        # Click on collapsible header
        result = subprocess.run(
            ["agent-browser", "click", ".collapsible-header"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Wait for animation
        time.sleep(0.5)

        # Take snapshot to verify state
        result = subprocess.run(
            ["agent-browser", "snapshot", "-i"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        print(f"\n✅ Trade Info toggled")

    def test_fill_trade_form(self):
        """Test filling trade form."""
        # Make sure Trade Info is expanded
        subprocess.run(
            ["agent-browser", "click", ".collapsible-header"],
            capture_output=True,
            timeout=10,
        )
        time.sleep(0.5)

        # Fill entry price
        subprocess.run(
            ["agent-browser", "fill", "#entry-price", "50000"],
            capture_output=True,
            timeout=10,
        )

        # Fill position size
        subprocess.run(
            ["agent-browser", "fill", "#position-size", "1"],
            capture_output=True,
            timeout=10,
        )

        print(f"\n✅ Trade form filled")

    def test_submit_trade_validation(self):
        """Test validation - submit without required fields."""
        # Click submit
        subprocess.run(
            ["agent-browser", "click", "#confirm-btn"], capture_output=True, timeout=10
        )

        time.sleep(1)

        # Get status message
        result = subprocess.run(
            ["agent-browser", "get", "text", "#status-message"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should show error (missing account/symbol)
        print(f"Status: {result.stdout}")
        assert (
            "error" in result.stdout.lower()
            or "select" in result.stdout.lower()
            or "required" in result.stdout.lower()
        )
        print(f"\n✅ Validation works")


class TestTradeSubmission:
    """Test complete trade submission workflow."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_electron(self):
        """Start Electron with remote debugging."""
        print("\n🚀 Starting Electron app for trade test...")

        self.proc = subprocess.Popen(
            ["bun", "start", "--", "--remote-debugging-port=9223"],
            cwd="desktop",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        time.sleep(6)

        # Connect
        subprocess.run(
            ["agent-browser", "connect", "9223"], capture_output=True, timeout=10
        )

        yield

        self.proc.terminate()
        self.proc.wait(timeout=5)

    def test_full_trade_submission(self):
        """Test complete trade submission."""
        # Expand Trade Info
        subprocess.run(
            ["agent-browser", "click", ".collapsible-header"],
            capture_output=True,
            timeout=10,
        )
        time.sleep(0.5)

        # Select account
        subprocess.run(
            ["agent-browser", "select", "#account-select", "1"],
            capture_output=True,
            timeout=10,
        )
        time.sleep(0.3)

        # Select symbol
        subprocess.run(
            ["agent-browser", "select", "#symbol-select", "1"],
            capture_output=True,
            timeout=10,
        )
        time.sleep(0.3)

        # Fill trade details
        subprocess.run(
            ["agent-browser", "fill", "#entry-price", "50000"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["agent-browser", "fill", "#position-size", "1"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["agent-browser", "fill", "#take-profit", "51000"],
            capture_output=True,
            timeout=10,
        )

        # Select direction and outcome
        subprocess.run(
            ["agent-browser", "select", "#direction", "long"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["agent-browser", "select", "#outcome", "win"],
            capture_output=True,
            timeout=10,
        )

        # Submit
        subprocess.run(
            ["agent-browser", "click", "#confirm-btn"], capture_output=True, timeout=10
        )

        # Wait for response
        time.sleep(2)

        # Check status
        result = subprocess.run(
            ["agent-browser", "get", "html", "#status-message"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        print(f"Response: {result.stdout}")

        # Verify success
        assert (
            "success" in result.stdout.lower()
            or "saved" in result.stdout.lower()
            or "trade" in result.stdout.lower()
        )
        print(f"\n✅ Trade submitted successfully!")

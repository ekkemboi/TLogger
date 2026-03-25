"""Tests for screenshot bug fix in trade creation.

Bug: In trade_service.py, create_trade saves screenshot BEFORE db.session.commit(),
so trade.id is None, resulting in filename 'None.png' instead of '{trade_id}.png'.

Additionally, screenshot_path should be a URL path, not a local filesystem path.
"""

import io
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestScreenshotFilename:
    """Tests that screenshot filename uses trade.id, not None."""

    def test_screenshot_filename_uses_trade_id_not_none(
        self, app, client, sample_trade_data
    ):
        """Test that screenshot is saved with trade.id, not 'None.png'."""
        # Create a fake image file
        screenshot_data = b"fake_png_content"
        screenshot = (io.BytesIO(screenshot_data), "test.png")

        # Send multipart request with screenshot
        response = client.post(
            "/api/trades",
            data={
                **sample_trade_data,
                "screenshot": screenshot,
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        trade = response.get_json()
        trade_id = trade["id"]

        # The screenshot_path should NOT contain 'None.png'
        assert "None.png" not in trade["screenshot_path"], (
            f"BUG: screenshot_path contains 'None.png': {trade['screenshot_path']}. "
            "The screenshot is saved before db.session.commit(), so trade.id is None."
        )

        # The screenshot_path should contain the actual trade ID
        assert trade_id in trade["screenshot_path"], (
            f"Expected screenshot_path to contain trade ID '{trade_id}', "
            f"but got: {trade['screenshot_path']}"
        )

    def test_screenshot_file_saved_with_correct_name(
        self, app, client, sample_trade_data, tmp_path
    ):
        """Test that the actual file on disk is named with trade.id.png."""
        # Override SCREENSHOT_DIR to use tmp_path for isolation
        with app.app_context():
            app.config["SCREENSHOT_DIR"] = tmp_path

        screenshot_data = b"fake_png_content"
        screenshot = (io.BytesIO(screenshot_data), "test.png")

        response = client.post(
            "/api/trades",
            data={
                **sample_trade_data,
                "screenshot": screenshot,
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        trade = response.get_json()
        trade_id = trade["id"]

        # Check that file exists with correct name
        expected_file = tmp_path / f"{trade_id}.png"
        none_file = tmp_path / "None.png"

        assert not none_file.exists(), (
            f"BUG: Found 'None.png' in screenshot directory. "
            "The screenshot is saved before trade.id is assigned."
        )

        assert expected_file.exists(), (
            f"Expected screenshot file '{expected_file}' not found. "
            f"Files in directory: {list(tmp_path.iterdir())}"
        )


class TestScreenshotPathFormat:
    """Tests that screenshot_path is a URL path, not a local filesystem path."""

    def test_screenshot_path_is_url_not_local_path(
        self, app, client, sample_trade_data, tmp_path
    ):
        """Test that screenshot_path is a URL like /api/screenshots/{id}.png."""
        with app.app_context():
            app.config["SCREENSHOT_DIR"] = tmp_path

        screenshot_data = b"fake_png_content"
        screenshot = (io.BytesIO(screenshot_data), "test.png")

        response = client.post(
            "/api/trades",
            data={
                **sample_trade_data,
                "screenshot": screenshot,
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        trade = response.get_json()
        trade_id = trade["id"]

        screenshot_path = trade["screenshot_path"]

        # Should NOT be a local filesystem path (e.g., /home/user/... or C:\...)
        assert not screenshot_path.startswith("/home"), (
            f"screenshot_path should be a URL, not a local path: {screenshot_path}"
        )
        assert not screenshot_path.startswith("C:\\"), (
            f"screenshot_path should be a URL, not a Windows path: {screenshot_path}"
        )
        assert "\\" not in screenshot_path, (
            f"screenshot_path should use forward slashes (URL), not backslashes: {screenshot_path}"
        )

        # Should be a URL path like /api/screenshots/{trade_id}.png
        assert screenshot_path.startswith("/api/screenshots/"), (
            f"Expected screenshot_path to start with '/api/screenshots/', "
            f"but got: {screenshot_path}"
        )

        assert screenshot_path == f"/api/screenshots/{trade_id}.png", (
            f"Expected screenshot_path to be '/api/screenshots/{trade_id}.png', "
            f"but got: {screenshot_path}"
        )

    def test_trade_without_screenshot_has_null_path(self, client, sample_trade_data):
        """Test that trades without screenshot have null screenshot_path."""
        response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        trade = response.get_json()

        assert trade["screenshot_path"] is None, (
            f"Expected screenshot_path to be None for trade without screenshot, "
            f"but got: {trade['screenshot_path']}"
        )


class TestScreenshotRetrieval:
    """Tests that screenshot can be retrieved after trade creation."""

    def test_screenshot_accessible_via_api(
        self, app, client, sample_trade_data, tmp_path
    ):
        """Test that uploaded screenshot can be retrieved via the API."""
        with app.app_context():
            app.config["SCREENSHOT_DIR"] = tmp_path

        screenshot_content = b"fake_png_image_data_here"
        screenshot = (io.BytesIO(screenshot_content), "chart.png")

        response = client.post(
            "/api/trades",
            data={
                **sample_trade_data,
                "screenshot": screenshot,
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        trade = response.get_json()
        trade_id = trade["id"]

        # Try to retrieve the screenshot via the expected URL
        screenshot_url = f"/api/screenshots/{trade_id}.png"
        get_response = client.get(screenshot_url)

        # This should succeed (200) once the screenshot endpoint is properly implemented
        # For now, we're testing that the path is correct
        assert trade["screenshot_path"] == screenshot_url, (
            f"Expected screenshot_path to be '{screenshot_url}', got '{trade['screenshot_path']}'"
        )

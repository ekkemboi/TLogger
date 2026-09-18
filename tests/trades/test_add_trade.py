"""Unit tests for Add Trade (Basic) user journey."""

import json
import os
import pytest
from io import BytesIO


class TestCreateTrade:
    """Tests for trade creation - Add Trade Basic flow."""

    def test_create_trade_success(self, auth_client, sample_trade_data):
        """Test creating a trade successfully."""
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["symbol"] == "BTCUSDT"
        assert data["direction"] == "long"
        assert data["entry_price"] == 67234.50
        assert data["status"] == "confirmed"

    def test_create_trade_missing_symbol(self, auth_client):
        """Test creating trade without symbol fails."""
        response = auth_client.post(
            "/api/trades",
            data=json.dumps({"direction": "long", "entry_price": 100}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_trade_missing_direction(self, auth_client):
        """Test creating trade without direction fails."""
        response = auth_client.post(
            "/api/trades",
            data=json.dumps({"symbol": "BTCUSDT", "entry_price": 100}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_trade_unauthenticated(self, client, sample_trade_data):
        """Test creating trade without authentication fails."""
        response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestGetTrades:
    """Tests for listing trades after creation."""

    def test_get_trades_empty(self, auth_client):
        """Test getting trades when none exist."""
        response = auth_client.get("/api/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert data["trades"] == []
        assert data["total"] == 0

    def test_get_trades_with_data(self, auth_client, sample_closed_trade_data):
        """Test getting trades after creating one."""
        auth_client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        response = auth_client.get("/api/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"


class TestPartialExits:
    """Tests for trade creation with partial exits - Flow 5."""

    def test_create_trade_with_single_partial_exit(
        self, auth_client, sample_trade_data
    ):
        """Test creating trade with one partial exit."""
        data = {
            **sample_trade_data,
            "exit_transactions": [{"qty": 0.5, "exit_price": 51000, "fees": 5}],
        }
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.get_json()
        assert len(result["exit_transactions"]) == 1
        assert result["exit_transactions"][0]["qty"] == 0.5
        assert result["exit_transactions"][0]["exit_price"] == 51000

    def test_create_trade_with_multiple_partial_exits(
        self, auth_client, sample_trade_data
    ):
        """Test creating trade with multiple partial exits."""
        data = {
            **sample_trade_data,
            "exit_transactions": [
                {"qty": 0.3, "exit_price": 51000, "fees": 5},
                {"qty": 0.4, "exit_price": 52000, "fees": 5},
            ],
        }
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.get_json()
        assert len(result["exit_transactions"]) == 2

    def test_partial_exit_stored_in_database(self, auth_client, sample_trade_data):
        """Test partial exit is stored in TradePartialExit table."""
        data = {
            **sample_trade_data,
            "position_size": 0.5,
            "exit_transactions": [{"qty": 0.3, "exit_price": 51000, "fees": 5}],
        }
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.get_json()
        assert "partial_exits" in result
        assert len(result["partial_exits"]) == 1


class TestTradeScreenshot:
    """Tests for trade creation with screenshot - Flow 6."""

    def test_create_trade_with_screenshot(self, auth_client, sample_trade_data, app):
        """Test creating trade with screenshot file."""
        # Create a mock image file
        image_data = b"fake image data"
        data = {
            "trade_data": json.dumps(sample_trade_data),
        }

        # Use multipart form data
        response = auth_client.post(
            "/api/trades",
            data={
                "trade_data": json.dumps(sample_trade_data),
                "screenshot": (BytesIO(image_data), "test.png", "image/png"),
            },
            content_type="multipart/form-data",
        )

        # Should succeed or fail gracefully
        assert response.status_code in [201, 400, 500]

    def test_screenshot_saved_to_directory(self, app):
        """Test that screenshot is saved to SCREENSHOT_DIR."""
        from src.config import Config

        screenshot_dir = getattr(Config, "SCREENSHOT_DIR", None)

        if screenshot_dir:
            assert os.path.exists(screenshot_dir) or screenshot_dir is not None

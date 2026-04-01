"""Tests for editing trade fields via PUT /api/trades/<id>."""

import json
import pytest


class TestEditTradeSymbol:
    """Tests for editing trade symbol."""

    def test_edit_symbol_success(self, client, sample_trade_data):
        """Test updating symbol changes it correctly."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["symbol"] == "BTCUSDT"

        # Update symbol
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"symbol": "ETHUSDT"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbol"] == "ETHUSDT"

    def test_edit_symbol_uppercase(self, client, sample_trade_data):
        """Test that lowercase symbol input becomes uppercase."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Update with lowercase symbol
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"symbol": "ethusdt"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbol"] == "ETHUSDT"


class TestEditTradeDirection:
    """Tests for editing trade direction."""

    def test_edit_direction_success(self, client, sample_trade_data):
        """Test changing direction from long to short."""
        # Create a long trade without TP/SL to avoid validation conflicts
        trade_data = {
            k: v
            for k, v in sample_trade_data.items()
            if k not in ["stop_loss", "take_profit"]
        }
        create_response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["direction"] == "long"

        # Update to short
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"direction": "short"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["direction"] == "short"

    def test_edit_direction_invalid(self, client, sample_trade_data):
        """Test that invalid direction returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try invalid direction
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"direction": "sideways"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestEditTradeEntryPrice:
    """Tests for editing trade entry price."""

    def test_edit_entry_price_success(self, client, sample_trade_data):
        """Test updating entry_price successfully."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["entry_price"] == 67234.50

        # Update entry price
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"entry_price": 68000.00}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["entry_price"] == 68000.00

    def test_edit_entry_price_invalid_zero(self, client, sample_trade_data):
        """Test that zero entry_price returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try zero entry price
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"entry_price": 0}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_edit_entry_price_invalid_negative(self, client, sample_trade_data):
        """Test that negative entry_price returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try negative entry price
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"entry_price": -100}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestEditTradeStopLoss:
    """Tests for editing trade stop loss."""

    def test_edit_stop_loss_success(self, client, sample_trade_data):
        """Test adding stop_loss to a trade."""
        # Create a trade without stop_loss
        trade_data = {k: v for k, v in sample_trade_data.items() if k != "stop_loss"}
        create_response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["stop_loss"] is None

        # Add stop loss
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"stop_loss": 66500.00}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["stop_loss"] == 66500.00

    def test_edit_stop_loss_null(self, client, sample_trade_data):
        """Test setting stop_loss to null removes it."""
        # Create a trade with stop_loss
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["stop_loss"] == 66800.00

        # Set stop loss to null
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"stop_loss": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["stop_loss"] is None


class TestEditTradePositionSize:
    """Tests for editing trade position size."""

    def test_edit_position_size_success(self, client, sample_trade_data):
        """Test updating position_size successfully."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        assert create_response.get_json()["position_size"] == 0.1

        # Update position size
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"position_size": 0.5}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["position_size"] == 0.5

    def test_edit_position_size_null(self, client, sample_trade_data):
        """Test setting position_size to null."""
        # Create a trade with position_size
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Set position size to null
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"position_size": None}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["position_size"] is None


class TestEditTradeValidation:
    """Tests for validation rules on trade edit."""

    def test_edit_empty_symbol(self, client, sample_trade_data):
        """Test that empty symbol string returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try empty symbol
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"symbol": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_edit_invalid_direction(self, client, sample_trade_data):
        """Test that invalid direction value returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try invalid direction
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"direction": "invalid"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_edit_negative_entry_price(self, client, sample_trade_data):
        """Test that negative entry_price returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try negative entry price
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"entry_price": -50}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_edit_negative_fees(self, client, sample_trade_data):
        """Test that negative fees returns 400."""
        # Create a trade
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        # Try negative fees
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"fees": -10}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestEditTradePnlRecalculation:
    """Tests for P&L recalculation after editing trade fields."""

    def test_pnl_recalculates_after_entry_price_change(
        self, client, sample_closed_trade_data
    ):
        """Test that P&L updates when entry_price changes."""
        # Create a closed trade with take_profit
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        original_pnl = create_response.get_json()["pnl"]
        # Original: (68500 - 67234.50) * 0.1 * 1 = 126.55
        assert original_pnl == pytest.approx(126.55, rel=1e-2)

        # Update entry price to a higher value
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"entry_price": 68000.00}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        # New P&L: (68500 - 68000) * 0.1 * 1 = 50.00
        assert data["pnl"] == pytest.approx(50.00, rel=1e-2)
        assert data["pnl"] != original_pnl

    def test_pnl_recalculates_after_symbol_change(
        self, client, sample_closed_trade_data
    ):
        """Test that P&L updates when symbol changes (different point_value)."""
        # Get user_id from sample data
        user_id = sample_closed_trade_data["user_id"]

        # Create a FavoriteProduct with custom point_value for ETHUSDT
        client.post(
            "/api/favorites",
            data=json.dumps(
                {"symbol": "ETHUSDT", "point_value": 0.1, "user_id": user_id}
            ),
            content_type="application/json",
        )

        # Create a closed trade with take_profit
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]
        original_pnl = create_response.get_json()["pnl"]
        # Original BTCUSDT: (68500 - 67234.50) * 0.1 * 1 = 126.55
        assert original_pnl == pytest.approx(126.55, rel=1e-2)

        # Change symbol to ETHUSDT (point_value = 0.1)
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"symbol": "ETHUSDT"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbol"] == "ETHUSDT"
        # New P&L: (68500 - 67234.50) * 0.1 * 0.1 = 12.655
        assert data["pnl"] == pytest.approx(12.655, rel=1e-2)
        assert data["pnl"] != original_pnl

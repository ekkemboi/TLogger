"""Tests for trade API endpoints."""

import json
import pytest


class TestCreateTrade:
    """Tests for POST /api/trades."""

    def test_create_trade_success(self, client, sample_trade_data):
        """Test creating a trade successfully."""
        response = client.post(
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

    def test_create_trade_missing_symbol(self, client):
        """Test creating trade without symbol fails."""
        response = client.post(
            "/api/trades",
            data=json.dumps({"direction": "long", "entry_price": 100}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_trade_missing_direction(self, client):
        """Test creating trade without direction fails."""
        response = client.post(
            "/api/trades",
            data=json.dumps({"symbol": "BTCUSDT", "entry_price": 100}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestGetTrades:
    """Tests for GET /api/trades."""

    def test_get_trades_empty(self, client):
        """Test getting trades when none exist."""
        response = client.get("/api/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert data["trades"] == []
        assert data["total"] == 0

    def test_get_trades_with_data(self, client, sample_closed_trade_data):
        """Test getting trades after creating one."""
        client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        response = client.get("/api/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"


class TestGetTrade:
    """Tests for GET /api/trades/:id."""

    def test_get_trade_success(self, client, sample_closed_trade_data):
        """Test getting a single trade."""
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        response = client.get(f"/api/trades/{trade_id}")
        assert response.status_code == 200
        assert response.get_json()["id"] == trade_id

    def test_get_trade_not_found(self, client):
        """Test getting non-existent trade."""
        response = client.get("/api/trades/nonexistent-id")
        assert response.status_code == 404


class TestUpdateTrade:
    """Tests for PUT /api/trades/:id."""

    def test_update_trade_exit_price(self, client, sample_trade_data):
        """Test updating trade with exit price."""
        # Create an open trade first (without take_profit)
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        assert create_response.get_json()["status"] == "confirmed"

        trade_id = create_response.get_json()["id"]

        # Now update it to close
        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps({"take_profit": 68000.00}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["take_profit"] == 68000.00
        assert data["status"] == "closed"
        assert data["pnl"] is not None


class TestDeleteTrade:
    """Tests for DELETE /api/trades/:id."""

    def test_delete_trade_success(self, client, sample_closed_trade_data):
        """Test deleting a trade."""
        create_response = client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        response = client.delete(f"/api/trades/{trade_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/api/trades/{trade_id}")
        assert get_response.status_code == 404

    def test_delete_trade_not_found(self, client):
        """Test deleting non-existent trade."""
        response = client.delete("/api/trades/nonexistent-id")
        assert response.status_code == 404

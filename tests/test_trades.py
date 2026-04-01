"""Tests for trade API endpoints."""

import json
import pytest


class TestCreateTrade:
    """Tests for POST /api/trades."""

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
    """Tests for GET /api/trades."""

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

    def test_get_trades_unauthenticated(self, client):
        """Test getting trades without authentication fails."""
        response = client.get("/api/trades")
        assert response.status_code == 401


class TestGetTrade:
    """Tests for GET /api/trades/:id."""

    def test_get_trade_success(self, auth_client, sample_closed_trade_data):
        """Test getting a single trade."""
        create_response = auth_client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        response = auth_client.get(f"/api/trades/{trade_id}")
        assert response.status_code == 200
        assert response.get_json()["id"] == trade_id

    def test_get_trade_not_found(self, auth_client):
        """Test getting non-existent trade."""
        response = auth_client.get("/api/trades/nonexistent-id")
        assert response.status_code == 404

    def test_get_trade_unauthenticated(self, client):
        """Test getting trade without authentication fails."""
        response = client.get("/api/trades/some-id")
        assert response.status_code == 401


class TestUpdateTrade:
    """Tests for PUT /api/trades/:id."""

    def test_update_trade_exit_price(self, auth_client, sample_trade_data):
        """Test updating trade with exit price."""
        # Create an open trade first (without take_profit)
        create_response = auth_client.post(
            "/api/trades",
            data=json.dumps(sample_trade_data),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        assert create_response.get_json()["status"] == "confirmed"

        trade_id = create_response.get_json()["id"]

        # Now update it to close
        response = auth_client.put(
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

    def test_delete_trade_success(self, auth_client, sample_closed_trade_data):
        """Test deleting a trade."""
        create_response = auth_client.post(
            "/api/trades",
            data=json.dumps(sample_closed_trade_data),
            content_type="application/json",
        )
        trade_id = create_response.get_json()["id"]

        response = auth_client.delete(f"/api/trades/{trade_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = auth_client.get(f"/api/trades/{trade_id}")
        assert get_response.status_code == 404

    def test_delete_trade_not_found(self, auth_client):
        """Test deleting non-existent trade."""
        response = auth_client.delete("/api/trades/nonexistent-id")
        assert response.status_code == 404

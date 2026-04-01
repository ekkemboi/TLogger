"""Tests for metrics API endpoint."""

import json
import pytest


class TestMetrics:
    """Tests for GET /api/metrics."""

    def test_metrics_empty(self, client):
        """Test metrics with no trades."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_trades"] == 0
        assert data["win_rate"] == 0
        assert data["total_pnl"] == 0

    def test_metrics_with_trades(self, client, default_account, default_user):
        """Test metrics with some trades."""
        # Create winning trade
        client.post(
            "/api/trades",
            data=json.dumps(
                {
                    "user_id": default_user,
                    "account_id": default_account,
                    "symbol": "BTCUSDT",
                    "direction": "long",
                    "entry_price": 67000,
                }
            ),
            content_type="application/json",
        )

        # Create losing trade
        client.post(
            "/api/trades",
            data=json.dumps(
                {
                    "user_id": default_user,
                    "account_id": default_account,
                    "symbol": "ETHUSDT",
                    "direction": "short",
                    "entry_price": 3500,
                }
            ),
            content_type="application/json",
        )

        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_trades"] == 2

"""Tests for metrics API endpoint."""

import json
import pytest


class TestMetrics:
    """Tests for GET /api/metrics."""

    def test_metrics_empty(self, auth_client):
        """Test metrics with no trades."""
        response = auth_client.get("/api/metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_trades"] == 0
        assert data["win_rate"] == 0
        assert data["total_pnl"] == 0

    def test_metrics_with_trades(self, auth_client, default_account):
        """Test metrics with some trades."""
        # Create winning trade
        auth_client.post(
            "/api/trades",
            data=json.dumps(
                {
                    "account_id": default_account,
                    "symbol": "BTCUSDT",
                    "direction": "long",
                    "entry_price": 67000,
                }
            ),
            content_type="application/json",
        )

        # Create losing trade
        auth_client.post(
            "/api/trades",
            data=json.dumps(
                {
                    "account_id": default_account,
                    "symbol": "ETHUSDT",
                    "direction": "short",
                    "entry_price": 3500,
                }
            ),
            content_type="application/json",
        )

        response = auth_client.get("/api/metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_trades"] == 2

    def test_metrics_unauthenticated(self, client):
        """Test metrics without authentication fails."""
        response = client.get("/api/metrics")
        assert response.status_code == 401

    def test_metrics_user_isolation(
        self, auth_client, app, default_user, default_account
    ):
        """Test that metrics only show current user's trades."""
        from src.models import Account, Trade, User, db
        from src.utils.password_utils import hash_password
        from src.utils.jwt_utils import generate_access_token

        # Create a trade for default_user
        auth_client.post(
            "/api/trades",
            data=json.dumps(
                {
                    "account_id": default_account,
                    "symbol": "BTCUSDT",
                    "direction": "long",
                    "entry_price": 67000,
                }
            ),
            content_type="application/json",
        )

        # Create another user with their own trade
        with app.app_context():
            other_user = User(
                email="other@example.com",
                name="Other User",
                password_hash=hash_password("OtherPass123!"),
                auth_provider="email",
            )
            db.session.add(other_user)
            db.session.commit()

            other_account = Account(name="Other Account", user_id=other_user.id)
            db.session.add(other_account)
            db.session.commit()

            # Create trade for other user directly in DB
            from src.models import TradeDirection, TradeStatus, TradeOutcome

            other_trade = Trade(
                user_id=other_user.id,
                account_id=other_account.id,
                symbol="ETHUSDT",
                direction=TradeDirection.SHORT,
                entry_price=3500,
                status=TradeStatus.CONFIRMED,
                outcome=TradeOutcome.WIN,
            )
            db.session.add(other_trade)
            db.session.commit()

        # Get metrics for default_user - should only see 1 trade
        response = auth_client.get("/api/metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_trades"] == 1  # Only sees their own trade

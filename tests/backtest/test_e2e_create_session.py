"""E2E integration tests for backtesting — create new session flow."""

import json
from datetime import datetime

import pytest
from src.models import Account, Asset, BacktestSession, PriceCandle, db


class TestCreateSessionE2E:
    """End-to-end test of the complete create session flow."""

    def test_full_create_session_flow(self, auth_client, app, default_user):
        """Complete flow: create asset → seed candles → create session → verify."""
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex", point_value=1, tick_size=0.00001, min_lot=0.01)
            db.session.add(asset)
            db.session.flush()
            for hour in range(20):
                c = PriceCandle(asset_id=asset.id, symbol="EURUSD", timeframe="1h", timestamp=datetime(2024, 1, 1, hour, 0), open=1.1, high=1.11, low=1.09, close=1.105)
                db.session.add(c)
            db.session.commit()

        payload = {
            "name": "E2E Test Session",
            "symbol": "EURUSD",
            "timeframe": "1h",
            "starting_balance": 10000,
        }
        response = auth_client.post(
            "/api/backtest/sessions",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()

        # Verify session
        session = data["session"]
        assert session["symbol"] == "EURUSD"
        assert session["timeframe"] == "1h"
        assert session["starting_balance"] == 10000.0
        assert session["current_balance"] == 10000.0
        assert session["status"] == "active"

        # Verify account was auto-created
        account = data["account"]
        assert account["is_backtest"] is True
        assert account["name"] == "E2E Test Session"
        assert account["opening_balance"] == 10000.0

        with app.app_context():
            db_account = Account.query.get(account["id"])
            assert db_account is not None
            assert db_account.is_backtest is True
            db_session = BacktestSession.query.get(session["id"])
            assert db_session is not None
            assert db_session.user_id == default_user

    def test_create_session_then_load_candles(self, auth_client, app, default_user):
        """Create session, then verify candles are accessible."""
        with app.app_context():
            asset = Asset(symbol="GBPUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()
            for hour in range(5):
                c = PriceCandle(asset_id=asset.id, symbol="GBPUSD", timeframe="1h", timestamp=datetime(2024, 1, 1, hour, 0), open=1.25, high=1.26, low=1.24, close=1.255)
                db.session.add(c)
            db.session.commit()

        auth_client.post(
            "/api/backtest/sessions",
            data=json.dumps({"name": "Candle Test", "symbol": "GBPUSD", "timeframe": "1h", "starting_balance": 5000}),
            content_type="application/json",
        )

        response = auth_client.get("/api/backtest/candles?symbol=GBPUSD&timeframe=1h")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candles"]) == 5

    def test_create_session_list_sessions(self, auth_client, app, default_user):
        """Create sessions, then list them."""
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.commit()

        for i in range(3):
            auth_client.post(
                "/api/backtest/sessions",
                data=json.dumps({"name": f"Session {i}", "symbol": "EURUSD", "timeframe": "1h", "starting_balance": 10000}),
                content_type="application/json",
            )

        response = auth_client.get("/api/backtest/sessions")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 3

    def test_create_session_account_appears_in_accounts(self, auth_client, app, default_user):
        """Auto-created backtest account shows up in accounts list."""
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.commit()

        auth_client.post(
            "/api/backtest/sessions",
            data=json.dumps({"name": "My Backtest", "symbol": "EURUSD", "timeframe": "1h", "starting_balance": 25000}),
            content_type="application/json",
        )

        response = auth_client.get("/api/accounts")
        assert response.status_code == 200
        data = response.get_json()
        backtest_accounts = [a for a in data["accounts"] if a.get("is_backtest")]
        assert len(backtest_accounts) >= 1
        assert backtest_accounts[0]["name"] == "My Backtest"

    def test_create_session_missing_name_fails(self, auth_client):
        response = auth_client.post(
            "/api/backtest/sessions",
            data=json.dumps({"symbol": "EURUSD", "timeframe": "1h", "starting_balance": 10000}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_session_unauthenticated(self, client):
        response = client.post(
            "/api/backtest/sessions",
            data=json.dumps({"name": "Test", "symbol": "EURUSD", "timeframe": "1h", "starting_balance": 10000}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_candle_data_empty(self, auth_client):
        response = auth_client.get("/api/backtest/candles?symbol=NONEXISTENT&timeframe=1h")
        assert response.status_code == 200
        data = response.get_json()
        assert data["candles"] == []

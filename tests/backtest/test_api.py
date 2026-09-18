"""Tests for backtest API endpoints."""

import json
from datetime import datetime, timedelta

import pytest
from src.models import Asset, BacktestSession, PriceCandle, Account, db


class TestBacktestAssetsAPI:
    """Tests for /api/backtest/assets endpoints."""

    ASSETS_URL = "/api/backtest/assets"

    def test_list_assets_empty(self, auth_client):
        response = auth_client.get(self.ASSETS_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert data["assets"] == []

    def test_list_assets_with_data(self, auth_client, app):
        with app.app_context():
            assets = [
                Asset(symbol="EURUSD", name="Euro/US Dollar", asset_type="forex"),
                Asset(symbol="BTCUSD", name="Bitcoin/USD", asset_type="crypto"),
                Asset(symbol="ES", name="E-mini S&P 500", asset_type="futures"),
            ]
            db.session.add_all(assets)
            db.session.commit()

        response = auth_client.get(self.ASSETS_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["assets"]) == 3

    def test_list_assets_only_active(self, auth_client, app):
        with app.app_context():
            assets = [
                Asset(symbol="EURUSD", asset_type="forex", is_active=True),
                Asset(symbol="DEAD", asset_type="forex", is_active=False),
            ]
            db.session.add_all(assets)
            db.session.commit()

        response = auth_client.get(self.ASSETS_URL)
        data = response.get_json()
        symbols = [a["symbol"] for a in data["assets"]]
        assert "EURUSD" in symbols
        assert "DEAD" not in symbols

    def test_list_assets_unauthenticated(self, client):
        response = client.get(self.ASSETS_URL)
        assert response.status_code == 401


class TestBacktestCandlesAPI:
    """Tests for /api/backtest/candles endpoints."""

    CANDLES_URL = "/api/backtest/candles"

    def test_get_candles_empty(self, auth_client):
        response = auth_client.get(f"{self.CANDLES_URL}?symbol=EURUSD&timeframe=1h")
        assert response.status_code == 200
        data = response.get_json()
        assert data["candles"] == []

    def test_get_candles_with_data(self, auth_client, app):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()
            for hour in range(5):
                c = PriceCandle(
                    asset_id=asset.id, symbol="EURUSD", timeframe="1h",
                    timestamp=datetime(2024, 1, 1, hour, 0),
                    open=1.1, high=1.11, low=1.09, close=1.105,
                )
                db.session.add(c)
            db.session.commit()

        response = auth_client.get(f"{self.CANDLES_URL}?symbol=EURUSD&timeframe=1h")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candles"]) == 5

    def test_get_candles_with_date_range(self, auth_client, app):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()
            for day in range(10):
                c = PriceCandle(
                    asset_id=asset.id, symbol="EURUSD", timeframe="1d",
                    timestamp=datetime(2024, 1, day + 1),
                    open=1.1, high=1.11, low=1.09, close=1.105,
                )
                db.session.add(c)
            db.session.commit()

        response = auth_client.get(f"{self.CANDLES_URL}?symbol=EURUSD&timeframe=1d&start=2024-01-03&end=2024-01-07")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candles"]) == 5

    def test_get_candles_missing_params(self, auth_client):
        response = auth_client.get(self.CANDLES_URL)
        assert response.status_code == 400

    def test_get_candles_pagination(self, auth_client):
        asset = Asset(symbol="EURUSD", asset_type="forex")
        db.session.add(asset)
        db.session.flush()
        for day in range(50):
            c = PriceCandle(
                asset_id=asset.id, symbol="EURUSD", timeframe="1d",
                timestamp=datetime(2024, 1, 1) + timedelta(days=day),
                open=1.1, high=1.11, low=1.09, close=1.105,
            )
            db.session.add(c)
        db.session.commit()

        response = auth_client.get(f"{self.CANDLES_URL}?symbol=EURUSD&timeframe=1d&page=1&per_page=20")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candles"]) == 20
        assert data["total"] == 50

    def test_get_candles_unauthenticated(self, client):
        response = client.get(f"{self.CANDLES_URL}?symbol=EURUSD&timeframe=1h")
        assert response.status_code == 401


class TestBacktestSessionsAPI:
    """Tests for /api/backtest/sessions endpoints."""

    SESSIONS_URL = "/api/backtest/sessions"

    def test_create_session(self, auth_client, app, default_user, default_account):
        payload = {
            "name": "Test Session",
            "symbol": "EURUSD",
            "timeframe": "1h",
            "starting_balance": 10000,
            "start_date": "2024-01-01T08:00:00",
        }
        response = auth_client.post(
            self.SESSIONS_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["session"]["symbol"] == "EURUSD"
        assert data["session"]["timeframe"] == "1h"
        assert data["session"]["starting_balance"] == 10000.0
        assert data["session"]["current_balance"] == 10000.0
        assert data["session"]["status"] == "active"
        assert data["account"]["is_backtest"] is True
        assert data["account"]["name"] == "Test Session"

    def test_create_session_missing_fields(self, auth_client):
        response = auth_client.post(
            self.SESSIONS_URL,
            data=json.dumps({"symbol": "EURUSD"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_session_unauthenticated(self, client):
        response = client.post(
            self.SESSIONS_URL,
            data=json.dumps({"symbol": "EURUSD", "timeframe": "1h", "starting_balance": 10000}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_list_sessions(self, auth_client, app, default_user):
        with app.app_context():
            sessions = [
                BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=10000),
                BacktestSession(user_id=default_user, symbol="BTCUSD", timeframe="4h", starting_balance=50000),
            ]
            db.session.add_all(sessions)
            db.session.commit()

        response = auth_client.get(self.SESSIONS_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 2

    def test_get_session_detail(self, auth_client, app, default_user):
        with app.app_context():
            session = BacktestSession(user_id=default_user, symbol="GBPUSD", timeframe="1h", starting_balance=25000)
            db.session.add(session)
            db.session.commit()
            session_id = session.id

        response = auth_client.get(f"{self.SESSIONS_URL}/{session_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbol"] == "GBPUSD"

    def test_get_session_not_found(self, auth_client):
        response = auth_client.get(f"{self.SESSIONS_URL}/nonexistent-id")
        assert response.status_code == 404

    def test_session_user_isolation(self, auth_client, app, default_user):
        with app.app_context():
            other_session = BacktestSession(user_id="other-user", symbol="EURUSD", timeframe="1h", starting_balance=1000)
            db.session.add(other_session)
            db.session.commit()

        response = auth_client.get(self.SESSIONS_URL)
        data = response.get_json()
        assert len(data["sessions"]) == 0


class TestBacktestControlsAPI:
    """Tests for session control endpoints (play/pause/stop/speed)."""

    CONTROLS_URL = "/api/backtest/sessions"

    def test_update_session_controls(self, auth_client, app, default_user):
        with app.app_context():
            session = BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=10000)
            db.session.add(session)
            db.session.commit()
            session_id = session.id

        response = auth_client.put(
            f"{self.CONTROLS_URL}/{session_id}/controls",
            data=json.dumps({"status": "paused"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "paused"

    def test_update_session_speed(self, auth_client, app, default_user):
        with app.app_context():
            session = BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=10000)
            db.session.add(session)
            db.session.commit()
            session_id = session.id

        response = auth_client.put(
            f"{self.CONTROLS_URL}/{session_id}/controls",
            data=json.dumps({"speed": 5}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_controls_unauthenticated(self, client, default_user):
        session = BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=10000)
        db.session.add(session)
        db.session.commit()

        response = client.put(
            f"{self.CONTROLS_URL}/{session.id}/controls",
            data=json.dumps({"status": "paused"}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestBacktestSummaryAPI:
    """Tests for session summary endpoint."""

    def test_get_session_summary(self, auth_client, default_user):
        session = BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=10000)
        db.session.add(session)
        db.session.commit()

        response = auth_client.get(f"{TestBacktestControlsAPI.CONTROLS_URL}/{session.id}/summary")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_trades" in data
        assert "win_rate" in data
        assert "total_pnl" in data
        assert "max_drawdown" in data

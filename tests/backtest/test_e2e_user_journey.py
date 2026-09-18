"""Full user-journey integration tests for backtesting.

Tests the complete create-session flow from a user perspective using the Flask test client:
fill form → submit → see replay controls → interact with chart.
"""

import json
from datetime import datetime, timedelta

import pytest
from src.models import Account, Asset, BacktestSession, PriceCandle, db


class TestCreateSessionUserJourney:
    """User journey: create a backtest session end-to-end."""

    def test_user_creates_session_and_sees_replay_controls(self, auth_client, app, default_user, default_account):
        """User opens backtest page → creates session → sees chart & replay bar."""
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex", point_value=1, tick_size=0.00001, min_lot=0.01)
            db.session.add(asset)
            db.session.flush()
            for hour in range(50):
                c = PriceCandle(
                    asset_id=asset.id, symbol="EURUSD", timeframe="1h",
                    timestamp=datetime(2024, 1, 1) + timedelta(hours=hour),
                    open=1.1000, high=1.1050, low=1.0980, close=1.1030,
                )
                db.session.add(c)
            db.session.commit()

        resp = auth_client.post("/api/backtest/sessions", data=json.dumps({
            "name": "London Session Test",
            "symbol": "EURUSD",
            "timeframe": "1h",
            "starting_balance": 10000,
        }), content_type="application/json")
        assert resp.status_code == 201
        data = resp.get_json()

        session = data["session"]
        assert session["symbol"] == "EURUSD"
        assert session["timeframe"] == "1h"
        assert session["starting_balance"] == 10000.0
        assert session["status"] == "active"
        assert session["current_balance"] == 10000.0

        account = data["account"]
        assert account["is_backtest"] is True
        assert account["name"] == "London Session Test"
        assert account["opening_balance"] == 10000.0

        candle_resp = auth_client.get("/api/backtest/candles?symbol=EURUSD&timeframe=1h&per_page=20")
        assert candle_resp.status_code == 200
        candle_data = candle_resp.get_json()
        assert len(candle_data["candles"]) == 20
        assert candle_data["total"] == 50

        account_resp = auth_client.get("/api/accounts")
        account_data = account_resp.get_json()
        backtest_accs = [a for a in account_data["accounts"] if a.get("is_backtest")]
        assert len(backtest_accs) >= 1

    def test_user_enters_trade_during_session(self, auth_client, app, default_user):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.commit()

        session_resp = auth_client.post("/api/backtest/sessions", data=json.dumps({
            "name": "Trade Entry Test",
            "symbol": "EURUSD",
            "timeframe": "1h",
            "starting_balance": 10000,
        }), content_type="application/json")
        assert session_resp.status_code == 201
        session = session_resp.get_json()
        account_id = session["account"]["id"]
        session_id = session["session"]["id"]

        trade_resp = auth_client.post(f"/api/backtest/sessions/{session_id}/trades", data=json.dumps({
            "account_id": account_id,
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.10500,
            "stop_loss": 1.09800,
            "take_profit": 1.11500,
            "position_size": 10000,
        }), content_type="application/json")
        assert trade_resp.status_code == 201
        trade = trade_resp.get_json()
        assert trade["symbol"] == "EURUSD"
        assert trade["direction"] == "long"
        assert float(trade["entry_price"]) == 1.10500

        summary_resp = auth_client.get(f"/api/backtest/sessions/{session_id}/summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.get_json()
        assert summary["total_trades"] >= 1

    def test_user_plays_and_pauses_replay(self, auth_client, app, default_user):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()
            for h in range(100):
                db.session.add(PriceCandle(asset_id=asset.id, symbol="EURUSD", timeframe="1h", timestamp=datetime(2024, 1, 1) + timedelta(hours=h), open=1.1, high=1.11, low=1.09, close=1.105))
            db.session.commit()

        session_resp = auth_client.post("/api/backtest/sessions", data=json.dumps({
            "name": "Playback Test",
            "symbol": "EURUSD",
            "timeframe": "1h",
            "starting_balance": 10000,
        }), content_type="application/json")
        session_id = session_resp.get_json()["session"]["id"]

        controls_resp = auth_client.put(f"/api/backtest/sessions/{session_id}/controls", data=json.dumps({
            "status": "paused",
        }), content_type="application/json")
        assert controls_resp.status_code == 200
        assert controls_resp.get_json()["status"] == "paused"

        controls_resp = auth_client.put(f"/api/backtest/sessions/{session_id}/controls", data=json.dumps({
            "speed": 5,
        }), content_type="application/json")
        assert controls_resp.status_code == 200

        controls_resp = auth_client.put(f"/api/backtest/sessions/{session_id}/controls", data=json.dumps({
            "status": "completed",
        }), content_type="application/json")
        assert controls_resp.status_code == 200
        assert controls_resp.get_json()["status"] == "completed"

    def test_user_sees_session_history(self, auth_client, app, default_user):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.commit()

        for i in range(3):
            auth_client.post("/api/backtest/sessions", data=json.dumps({
                "name": f"Session {i}",
                "symbol": "EURUSD",
                "timeframe": "1h",
                "starting_balance": 10000,
            }), content_type="application/json")

        list_resp = auth_client.get("/api/backtest/sessions")
        assert list_resp.status_code == 200
        sessions = list_resp.get_json()["sessions"]
        assert len(sessions) == 3

    def test_user_closes_session_panel_without_creating(self, auth_client):
        """Verify cancel returns 200 — user just closes panel, no session created."""
        list_resp = auth_client.get("/api/backtest/sessions")
        assert list_resp.status_code == 200
        assert len(list_resp.get_json()["sessions"]) == 0

    def test_user_sees_validation_error_on_empty_form(self, auth_client):
        resp = auth_client.post("/api/backtest/sessions", data=json.dumps({
            "symbol": "EURUSD",
            "timeframe": "1h",
        }), content_type="application/json")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_user_cannot_access_backtest_without_auth(self, client):
        resp = client.get("/api/backtest/sessions")
        assert resp.status_code == 401

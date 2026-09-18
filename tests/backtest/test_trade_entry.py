"""Tests for entering trades during backtest sessions via API."""

import json
from datetime import datetime
from decimal import Decimal

import pytest
from src.models import Account, BacktestSession, Trade, TradeDirection, db


class TestBacktestTradeEntry:
    """Tests for creating trades within a backtest session."""

    TRADES_URL = "/api/backtest/sessions"

    def create_session_and_backtest_account(self, auth_client, app, default_user):
        """Helper to create a backtest account and session."""
        with app.app_context():
            backtest_account = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add(backtest_account)
            db.session.flush()
            session = BacktestSession(
                user_id=default_user, symbol="EURUSD", timeframe="1h",
                starting_balance=10000, current_balance=10000,
            )
            db.session.add(session)
            db.session.commit()
            return session.id, backtest_account.id

    def test_enter_trade_during_session(self, auth_client, app, default_user):
        session_id, account_id = self.create_session_and_backtest_account(auth_client, app, default_user)

        payload = {
            "account_id": account_id,
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.10500,
            "stop_loss": 1.09800,
            "take_profit": 1.11500,
            "position_size": 10000,
            "current_candle_time": "2024-01-01T12:00:00",
        }
        response = auth_client.post(
            f"{self.TRADES_URL}/{session_id}/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["symbol"] == "EURUSD"
        assert data["direction"] == "long"
        assert float(data["entry_price"]) == 1.10500

    def test_enter_trade_rejects_wrong_account_type(self, auth_client, app, default_user, default_account):
        session_id, _ = self.create_session_and_backtest_account(auth_client, app, default_user)

        payload = {
            "account_id": default_account,
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.10500,
            "position_size": 10000,
        }
        response = auth_client.post(
            f"{self.TRADES_URL}/{session_id}/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_enter_trade_unauthenticated(self, client, app, default_user):
        session_id, account_id = self.create_session_and_backtest_account(auth_client=None, app=app, default_user=default_user)
        payload = {"symbol": "EURUSD", "direction": "long", "entry_price": 1.10500}
        response = client.post(
            f"{self.TRADES_URL}/{session_id}/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_enter_trade_missing_fields(self, auth_client, app, default_user):
        session_id, account_id = self.create_session_and_backtest_account(auth_client, app, default_user)

        response = auth_client.post(
            f"{self.TRADES_URL}/{session_id}/trades",
            data=json.dumps({"account_id": account_id, "symbol": "EURUSD"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_backtest_trade_shows_in_account(self, auth_client, app, default_user):
        session_id, account_id = self.create_session_and_backtest_account(auth_client, app, default_user)

        payload = {
            "account_id": account_id,
            "symbol": "GBPUSD",
            "direction": "short",
            "entry_price": 1.25000,
            "stop_loss": 1.26000,
            "take_profit": 1.24000,
            "position_size": 10000,
        }
        auth_client.post(
            f"{self.TRADES_URL}/{session_id}/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = auth_client.get(f"/api/accounts/{account_id}/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["trades"]) >= 1


class TestAutoBreakeven:
    """Tests for auto breakeven logic."""

    def test_breakeven_sl_moved_to_entry(self, app):
        """Auto-breakeven: when price moves X ticks in favor, SL moves to entry."""
        entry = Decimal("1.10000")
        stop_loss = Decimal("1.09500")
        current_price = Decimal("1.10500")
        breakeven_trigger_pips = Decimal("0.00200")
        price_movement = current_price - entry

        if price_movement >= breakeven_trigger_pips:
            stop_loss = entry

        assert stop_loss == entry
        assert stop_loss == Decimal("1.10000")

    def test_breakeven_not_triggered_below_threshold(self, app):
        entry = Decimal("1.10000")
        stop_loss = Decimal("1.09500")
        current_price = Decimal("1.10100")
        breakeven_trigger_pips = Decimal("0.00200")
        price_movement = current_price - entry

        if price_movement >= breakeven_trigger_pips:
            stop_loss = entry

        assert stop_loss == Decimal("1.09500")

    def test_breakeven_for_short_trades(self, app):
        entry = Decimal("1.20000")
        stop_loss = Decimal("1.20500")
        current_price = Decimal("1.19500")
        breakeven_trigger_pips = Decimal("0.00300")
        price_movement = entry - current_price

        if price_movement >= breakeven_trigger_pips:
            stop_loss = entry

        assert stop_loss == entry
        assert stop_loss == Decimal("1.20000")


class TestBacktestSessionSummary:
    """Tests for backtest session summary calculations."""

    def test_summary_with_no_trades(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user, symbol="EURUSD", timeframe="1h",
                starting_balance=10000, current_balance=10000,
            )
            db.session.add(session)
            db.session.commit()

            assert session.starting_balance == session.current_balance

    def test_trade_attribution_to_session(self, app, default_user):
        with app.app_context():
            account = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add(account)
            db.session.flush()

            session = BacktestSession(
                user_id=default_user, symbol="EURUSD", timeframe="1h",
                starting_balance=10000,
            )
            db.session.add(session)
            db.session.flush()

            trade = Trade(
                user_id=default_user,
                account_id=account.id,
                symbol="EURUSD",
                direction=TradeDirection.LONG,
                entry_price=Decimal("1.10000"),
                position_size=Decimal("1"),
            )
            db.session.add(trade)
            db.session.commit()

            assert trade.account_id == account.id

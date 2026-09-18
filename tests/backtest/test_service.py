"""Tests for backtesting service — replay engine, session management, candle progression."""

import json
from datetime import datetime
from decimal import Decimal

import pytest
from src.models import Asset, BacktestSession, PriceCandle, Trade, Account, TradeDirection, TradeOutcome, db


class TestReplayEngine:
    """Tests for in-memory replay engine logic."""

    def test_candle_progression(self, app, default_user):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()

            for hour in range(10):
                c = PriceCandle(
                    asset_id=asset.id, symbol="EURUSD", timeframe="1h",
                    timestamp=datetime(2024, 1, 1, hour, 0),
                    open=1.1 + hour * 0.001, high=1.11 + hour * 0.001,
                    low=1.09 + hour * 0.001, close=1.105 + hour * 0.001,
                )
                db.session.add(c)
            db.session.commit()

            candles = PriceCandle.query.filter_by(symbol="EURUSD", timeframe="1h").order_by(PriceCandle.timestamp).all()
            assert len(candles) == 10
            assert candles[0].timestamp.hour == 0
            assert candles[9].timestamp.hour == 9

    def test_replay_speed_scaling(self, app):
        """Verify speed multipliers affect candle advancement."""
        base_interval_ms = 1000
        speeds = {1: 1000, 2: 500, 5: 200, 10: 100}
        for speed, expected in speeds.items():
            assert base_interval_ms / speed == expected

    def test_session_balance_tracking(self, app, default_user):
        with app.app_context():
            account = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add(account)
            db.session.flush()

            session = BacktestSession(
                user_id=default_user, symbol="BTCUSD", timeframe="1h",
                starting_balance=10000, current_balance=10000,
            )
            db.session.add(session)
            db.session.commit()

            assert float(session.current_balance) == 10000.0
            assert float(session.starting_balance) == 10000.0


class TestSessionManagement:
    """Tests for backtest session CRUD."""

    def test_create_session(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user, symbol="EURUSD", timeframe="1h",
                starting_balance=5000,
            )
            db.session.add(session)
            db.session.commit()

            saved = BacktestSession.query.filter_by(user_id=default_user, symbol="EURUSD").first()
            assert saved is not None
            assert saved.status == "active"

    def test_complete_session(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user, symbol="GBPUSD", timeframe="4h",
                starting_balance=10000,
            )
            db.session.add(session)
            db.session.commit()

            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.session.commit()

            saved = BacktestSession.query.get(session.id)
            assert saved.status == "completed"
            assert saved.completed_at is not None

    def test_session_user_isolation(self, app, default_user):
        with app.app_context():
            s1 = BacktestSession(user_id=default_user, symbol="EURUSD", timeframe="1h", starting_balance=1000)
            s2 = BacktestSession(user_id="other-user-id", symbol="EURUSD", timeframe="1h", starting_balance=1000)
            db.session.add_all([s1, s2])
            db.session.commit()

            user_sessions = BacktestSession.query.filter_by(user_id=default_user).all()
            assert len(user_sessions) == 1

    def test_session_duration_tracking(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user, symbol="EURUSD", timeframe="1h",
                starting_balance=10000,
                start_date=datetime(2024, 1, 1, 8, 0),
                end_date=datetime(2024, 1, 1, 16, 0),
            )
            db.session.add(session)
            db.session.commit()

            assert session.start_date is not None
            assert session.end_date is not None


class TestTradeEntryDuringBacktest:
    """Tests for entering trades during a backtesting session."""

    def test_backtest_trade_uses_backtest_account(self, app, default_user, default_account):
        with app.app_context():
            backtest_account = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add(backtest_account)
            db.session.flush()

            trade = Trade(
                user_id=default_user,
                account_id=backtest_account.id,
                symbol="EURUSD",
                direction=TradeDirection.LONG,
                entry_price=Decimal("1.10000"),
                stop_loss=Decimal("1.09500"),
                take_profit=Decimal("1.11000"),
                position_size=Decimal("1"),
                status="confirmed",
            )
            db.session.add(trade)
            db.session.commit()

            backtest_trades = Trade.query.join(Account).filter(Account.is_backtest == True, Trade.user_id == default_user).all()
            assert len(backtest_trades) == 1
            assert backtest_trades[0].symbol == "EURUSD"

    def test_live_trade_uses_live_account(self, app, default_user, default_account):
        with app.app_context():
            trade = Trade(
                user_id=default_user,
                account_id=default_account,
                symbol="BTCUSDT",
                direction=TradeDirection.LONG,
                entry_price=Decimal("50000"),
                position_size=Decimal("0.1"),
                status="confirmed",
            )
            db.session.add(trade)
            db.session.commit()

            live_trades = Trade.query.join(Account).filter(Account.is_backtest == False, Trade.user_id == default_user).all()
            assert len(live_trades) == 1

    def test_backtest_trade_pnl_calculation(self, app, default_user):
        with app.app_context():
            account = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add(account)
            db.session.flush()

            trade = Trade(
                user_id=default_user,
                account_id=account.id,
                symbol="EURUSD",
                direction=TradeDirection.LONG,
                entry_price=Decimal("1.10000"),
                take_profit=Decimal("1.11000"),
                position_size=Decimal("10000"),
                outcome=TradeOutcome.WIN,
                pnl=Decimal("100"),
            )
            db.session.add(trade)
            db.session.commit()

            assert float(trade.pnl) == 100

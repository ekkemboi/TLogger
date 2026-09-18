"""Tests for backtesting models — Asset, PriceCandle, BacktestSession, Account.is_backtest."""

import uuid
from datetime import datetime, date

import pytest
from src.models import Account, Asset, BacktestSession, PriceCandle, db


class TestAssetModel:
    """Tests for Asset model."""

    def test_create_asset(self, app):
        with app.app_context():
            asset = Asset(
                symbol="EURUSD",
                name="Euro/US Dollar",
                asset_type="forex",
                point_value=1,
                tick_size=0.00001,
                min_lot=0.01,
            )
            db.session.add(asset)
            db.session.commit()

            saved = Asset.query.filter_by(symbol="EURUSD").first()
            assert saved is not None
            assert saved.symbol == "EURUSD"
            assert saved.asset_type == "forex"
            assert saved.point_value == 1
            assert saved.is_active is True

    def test_asset_to_dict(self, app):
        with app.app_context():
            asset = Asset(symbol="BTCUSD", name="Bitcoin/US Dollar", asset_type="crypto")
            db.session.add(asset)
            db.session.commit()

            d = asset.to_dict()
            assert d["symbol"] == "BTCUSD"
            assert d["asset_type"] == "crypto"

    def test_asset_unique_symbol(self, app):
        with app.app_context():
            a1 = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(a1)
            db.session.commit()

            a2 = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(a2)
            with pytest.raises(Exception):
                db.session.commit()

    def test_asset_default_active(self, app):
        with app.app_context():
            asset = Asset(symbol="GBPUSD", asset_type="forex")
            db.session.add(asset)
            db.session.commit()
            assert asset.is_active is True


class TestPriceCandleModel:
    """Tests for PriceCandle model."""

    def test_create_candle(self, app):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()

            candle = PriceCandle(
                asset_id=asset.id,
                symbol="EURUSD",
                timeframe="1h",
                timestamp=datetime(2024, 1, 1, 12, 0),
                open=1.10000,
                high=1.10500,
                low=1.09800,
                close=1.10300,
                volume=1000,
            )
            db.session.add(candle)
            db.session.commit()

            saved = PriceCandle.query.filter_by(symbol="EURUSD", timeframe="1h").first()
            assert saved is not None
            assert float(saved.open) == 1.10000
            assert float(saved.high) == 1.10500
            assert float(saved.low) == 1.09800
            assert float(saved.close) == 1.10300

    def test_candle_indexed_by_symbol_timeframe_timestamp(self, app):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()

            ts1 = datetime(2024, 1, 1, 12, 0)
            ts2 = datetime(2024, 1, 1, 13, 0)
            c1 = PriceCandle(asset_id=asset.id, symbol="EURUSD", timeframe="1h", timestamp=ts1, open=1.1, high=1.11, low=1.09, close=1.105)
            c2 = PriceCandle(asset_id=asset.id, symbol="EURUSD", timeframe="1h", timestamp=ts2, open=1.105, high=1.115, low=1.095, close=1.11)
            db.session.add_all([c1, c2])
            db.session.commit()

            candles = PriceCandle.query.filter_by(symbol="EURUSD", timeframe="1h").order_by(PriceCandle.timestamp).all()
            assert len(candles) == 2
            assert candles[0].timestamp == ts1
            assert candles[1].timestamp == ts2

    def test_candle_query_range(self, app):
        with app.app_context():
            asset = Asset(symbol="EURUSD", asset_type="forex")
            db.session.add(asset)
            db.session.flush()

            for hour in range(24):
                c = PriceCandle(asset_id=asset.id, symbol="EURUSD", timeframe="1h", timestamp=datetime(2024, 1, 1, hour, 0), open=1.1, high=1.11, low=1.09, close=1.105)
                db.session.add(c)
            db.session.commit()

            result = PriceCandle.query.filter(
                PriceCandle.symbol == "EURUSD",
                PriceCandle.timeframe == "1h",
                PriceCandle.timestamp >= datetime(2024, 1, 1, 8, 0),
                PriceCandle.timestamp <= datetime(2024, 1, 1, 16, 0),
            ).count()
            assert result == 9


class TestBacktestSessionModel:
    """Tests for BacktestSession model."""

    def test_create_session(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user,
                symbol="EURUSD",
                timeframe="1h",
                starting_balance=10000,
                current_balance=10000,
                status="active",
            )
            db.session.add(session)
            db.session.commit()

            saved = BacktestSession.query.filter_by(user_id=default_user).first()
            assert saved is not None
            assert saved.symbol == "EURUSD"
            assert saved.starting_balance == 10000
            assert saved.current_balance == 10000
            assert saved.status == "active"

    def test_session_default_values(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user,
                symbol="BTCUSD",
                timeframe="1d",
                starting_balance=50000,
                current_balance=50000,
            )
            db.session.add(session)
            db.session.commit()

            assert float(session.current_balance) == 50000
            assert session.status == "active"
            assert session.created_at is not None

    def test_session_to_dict(self, app, default_user):
        with app.app_context():
            session = BacktestSession(
                user_id=default_user,
                symbol="GBPUSD",
                timeframe="4h",
                starting_balance=25000,
            )
            db.session.add(session)
            db.session.commit()

            d = session.to_dict()
            assert d["symbol"] == "GBPUSD"
            assert d["timeframe"] == "4h"
            assert d["starting_balance"] == 25000.0


class TestAccountBacktestFlag:
    """Tests for is_backtest flag on Account model."""

    def test_account_default_not_backtest(self, app, default_user):
        with app.app_context():
            account = Account(name="Live Trading", user_id=default_user)
            db.session.add(account)
            db.session.commit()
            assert account.is_backtest is False

    def test_create_backtest_account(self, app, default_user):
        with app.app_context():
            account = Account(name="Backtest Account", user_id=default_user, is_backtest=True)
            db.session.add(account)
            db.session.commit()

            saved = Account.query.filter_by(user_id=default_user, is_backtest=True).first()
            assert saved is not None
            assert saved.name == "Backtest Account"
            assert saved.is_backtest is True

    def test_multiple_accounts_mixed_types(self, app, default_user):
        with app.app_context():
            live = Account(name="Live Account", user_id=default_user, is_backtest=False)
            backtest = Account(name="Backtest", user_id=default_user, is_backtest=True)
            db.session.add_all([live, backtest])
            db.session.commit()

            accounts = Account.query.filter_by(user_id=default_user).all()
            assert len(accounts) == 2

            backtest_accounts = Account.query.filter_by(user_id=default_user, is_backtest=True).all()
            assert len(backtest_accounts) == 1

    def test_backtest_account_in_to_dict(self, app, default_user):
        with app.app_context():
            account = Account(name="Test Backtest", user_id=default_user, is_backtest=True)
            db.session.add(account)
            db.session.commit()

            d = account.to_dict()
            assert d["is_backtest"] is True

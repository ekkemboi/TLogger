"""Tests for advanced analytics — time-based, calendar, Monte Carlo, drawdown, tags."""

import json
from datetime import datetime, date
from decimal import Decimal

import pytest
from src.models import Account, Trade, TradeDirection, TradeOutcome, db


class TestTimeBasedAnalytics:
    """Tests for time-based analytics endpoints."""

    ANALYTICS_URL = "/api/analytics"

    def _create_trades(self, app, default_user, default_account, count=5):
        with app.app_context():
            for i in range(count):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    exit_price=Decimal("1.10500"),
                    take_profit=Decimal("1.10500"),
                    position_size=Decimal("1"),
                    outcome=TradeOutcome.WIN if i % 2 == 0 else TradeOutcome.LOSS,
                    pnl=Decimal("50") if i % 2 == 0 else Decimal("-50"),
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

    def test_time_based_hourly(self, auth_client, app, default_user, default_account):
        self._create_trades(app, default_user, default_account)
        response = auth_client.get(f"{self.ANALYTICS_URL}/time-based?group_by=hour")
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data

    def test_time_based_daily(self, auth_client, app, default_user, default_account):
        self._create_trades(app, default_user, default_account)
        response = auth_client.get(f"{self.ANALYTICS_URL}/time-based?group_by=day")
        assert response.status_code == 200

    def test_time_based_by_session(self, auth_client, app, default_user, default_account):
        self._create_trades(app, default_user, default_account)
        response = auth_client.get(f"{self.ANALYTICS_URL}/time-based?group_by=session")
        assert response.status_code == 200

    def test_time_based_no_trades(self, auth_client):
        response = auth_client.get(f"{self.ANALYTICS_URL}/time-based?group_by=hour")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 0


class TestPerformanceCalendar:
    """Tests for performance calendar analytics."""

    def test_calendar_with_trades(self, auth_client, app, default_user, default_account):
        with app.app_context():
            for day in range(1, 31):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    position_size=Decimal("1"),
                    outcome=TradeOutcome.WIN if day % 2 == 0 else TradeOutcome.LOSS,
                    pnl=Decimal("100") if day % 2 == 0 else Decimal("-50"),
                    trade_date=date(2024, 1, day),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.get("/api/analytics/calendar?year=2024&month=1")
        assert response.status_code == 200
        data = response.get_json()
        assert "days" in data
        assert len(data["days"]) == 30

    def test_calendar_empty_range(self, auth_client):
        response = auth_client.get("/api/analytics/calendar?year=2024&month=6")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["days"]) == 0


class TestMonteCarloSimulation:
    """Tests for Monte Carlo simulation."""

    def test_monte_carlo_runs(self, auth_client, app, default_user, default_account):
        with app.app_context():
            outcomes = [100, -50, 75, -25, 200, -100, 50, -30, 150, -60]
            for i, pnl in enumerate(outcomes):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    position_size=Decimal("1"),
                    outcome=TradeOutcome.WIN if pnl > 0 else TradeOutcome.LOSS,
                    pnl=Decimal(str(pnl)),
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.post("/api/analytics/monte-carlo", data=json.dumps({"simulations": 100}), content_type="application/json")
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_monte_carlo_requires_trades(self, auth_client):
        response = auth_client.post("/api/analytics/monte-carlo", data=json.dumps({"simulations": 100}), content_type="application/json")
        assert response.status_code == 400


class TestDrawdownAnalysis:
    """Tests for drawdown analytics."""

    def test_drawdown_with_trades(self, auth_client, app, default_user, default_account):
        with app.app_context():
            pnls = [100, 200, -50, -100, 300, -200, 150, -75, 50, 100]
            for i, pnl in enumerate(pnls):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    outcome=TradeOutcome.WIN if pnl > 0 else TradeOutcome.LOSS,
                    pnl=Decimal(str(pnl)),
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.get("/api/analytics/drawdown")
        assert response.status_code == 200
        data = response.get_json()
        assert "max_drawdown" in data
        assert "average_drawdown" in data


class TestTagAnalytics:
    """Tests for tag combination analysis."""

    def test_tag_analysis(self, auth_client, app, default_user, default_account):
        with app.app_context():
            tags_list = [
                ["breakout", "london"],
                ["breakout", "london"],
                ["reversal", "ny"],
                ["breakout", "ny"],
                ["reversal", "london"],
            ]
            for i, tags in enumerate(tags_list):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    outcome=TradeOutcome.WIN if i < 3 else TradeOutcome.LOSS,
                    pnl=Decimal("100") if i < 3 else Decimal("-50"),
                    tags=tags,
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.get("/api/analytics/tags")
        assert response.status_code == 200
        data = response.get_json()
        assert "combinations" in data


class TestEquityCurve:
    """Tests for equity curve data."""

    def test_equity_curve(self, auth_client, app, default_user, default_account):
        with app.app_context():
            for i in range(20):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    outcome=TradeOutcome.WIN,
                    pnl=Decimal("100"),
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.get("/api/analytics/equity")
        assert response.status_code == 200
        data = response.get_json()
        assert "points" in data
        assert len(data["points"]) == 20


class TestRiskMetrics:
    """Tests for risk metrics (Sharpe ratio, etc.)."""

    def test_risk_metrics(self, auth_client, app, default_user, default_account):
        with app.app_context():
            for i in range(20):
                t = Trade(
                    user_id=default_user,
                    account_id=default_account,
                    symbol="EURUSD",
                    direction=TradeDirection.LONG,
                    entry_price=Decimal("1.10000"),
                    take_profit=Decimal("1.11000"),
                    position_size=Decimal("1"),
                    outcome=TradeOutcome.WIN if i % 2 == 0 else TradeOutcome.LOSS,
                    pnl=Decimal("100") if i % 2 == 0 else Decimal("-50"),
                    trade_date=date(2024, 1, i + 1),
                )
                db.session.add(t)
            db.session.commit()

        response = auth_client.get("/api/analytics/risk-metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert "sharpe_ratio" in data
        assert "profit_factor" in data
        assert "total_trades" in data


class TestAnalyticsUnauthenticated:
    """Tests that analytics endpoints require auth."""

    def test_unauthenticated_access(self, client):
        endpoints = ["/api/analytics/time-based", "/api/analytics/calendar", "/api/analytics/drawdown", "/api/analytics/equity", "/api/analytics/tags", "/api/analytics/risk-metrics"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_monte_carlo_unauthenticated(self, client):
        response = client.post("/api/analytics/monte-carlo", data=json.dumps({"simulations": 100}), content_type="application/json")
        assert response.status_code == 401

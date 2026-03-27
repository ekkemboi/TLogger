"""Tests for trade outcome field and outcome-based P&L calculation."""

import json
import pytest


class TestTradeOutcomeWin:
    """Tests for trades with outcome=WIN (P&L uses take_profit)."""

    def test_outcome_win_long(self, client, default_account):
        """LONG trade with outcome=WIN uses take_profit as exit price for P&L."""
        # Entry: 100, TP: 120, SL: 90, Size: 1, Fees: 5
        # P&L = (120 - 100) * 1 * 1 - 5 = 15
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 100.00,
            "take_profit": 120.00,
            "stop_loss": 90.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "WIN",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "win"
        assert data["pnl"] == 15.00

    def test_outcome_win_short(self, client, default_account):
        """SHORT trade with outcome=WIN uses take_profit as exit price for P&L."""
        # Entry: 100, TP: 80, SL: 110, Size: 1, Fees: 5
        # P&L = (100 - 80) * 1 * 1 - 5 = 15
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "short",
            "entry_price": 100.00,
            "take_profit": 80.00,
            "stop_loss": 110.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "WIN",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "win"
        assert data["pnl"] == 15.00


class TestTradeOutcomeLoss:
    """Tests for trades with outcome=LOSS (P&L uses stop_loss)."""

    def test_outcome_loss_long(self, client, default_account):
        """LONG trade with outcome=LOSS uses stop_loss as exit price for P&L."""
        # Entry: 100, TP: 120, SL: 90, Size: 1, Fees: 5
        # P&L = (90 - 100) * 1 * 1 - 5 = -15
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 100.00,
            "take_profit": 120.00,
            "stop_loss": 90.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "LOSS",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "loss"
        assert data["pnl"] == -15.00

    def test_outcome_loss_short(self, client, default_account):
        """SHORT trade with outcome=LOSS uses stop_loss as exit price for P&L."""
        # Entry: 100, TP: 80, SL: 110, Size: 1, Fees: 5
        # P&L = (100 - 110) * 1 * 1 - 5 = -15
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "short",
            "entry_price": 100.00,
            "take_profit": 80.00,
            "stop_loss": 110.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "LOSS",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "loss"
        assert data["pnl"] == -15.00


class TestTradeOutcomeBreakEven:
    """Tests for trades with outcome=BREAK_EVEN (P&L = -fees only)."""

    def test_outcome_break_even_long(self, client, default_account):
        """LONG trade with outcome=BREAK_EVEN has P&L = -fees only."""
        # Entry: 100, TP: 120, SL: 90, Size: 1, Fees: 5
        # P&L = -5 (only fees, no price movement counted)
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 100.00,
            "take_profit": 120.00,
            "stop_loss": 90.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "BREAK_EVEN",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "break_even"
        assert data["pnl"] == -5.00

    def test_outcome_break_even_short(self, client, default_account):
        """SHORT trade with outcome=BREAK_EVEN has P&L = -fees only."""
        # Entry: 100, TP: 80, SL: 110, Size: 1, Fees: 5
        # P&L = -5 (only fees, no price movement counted)
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "short",
            "entry_price": 100.00,
            "take_profit": 80.00,
            "stop_loss": 110.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "BREAK_EVEN",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "break_even"
        assert data["pnl"] == -5.00


class TestTradeOutcomeDefault:
    """Tests for default outcome behavior."""

    def test_default_outcome_is_win(self, client, default_account):
        """Trade created without outcome field defaults to WIN."""
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 100.00,
            "take_profit": 120.00,
            "stop_loss": 90.00,
            "position_size": 1.0,
            "fees": 5.00,
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["outcome"] == "win"
        # P&L should use take_profit: (120 - 100) * 1 * 1 - 5 = 15
        assert data["pnl"] == 15.00


class TestTradeOutcomeValidation:
    """Tests for outcome field validation."""

    def test_invalid_outcome(self, client, default_account):
        """Invalid outcome value returns 400."""
        trade_data = {
            "account_id": default_account,
            "symbol": "BTCUSDT",
            "direction": "long",
            "entry_price": 100.00,
            "take_profit": 120.00,
            "stop_loss": 90.00,
            "position_size": 1.0,
            "fees": 5.00,
            "outcome": "INVALID_VALUE",
        }
        response = client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

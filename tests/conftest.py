"""Test fixtures for TradeLogger."""

import pytest
from src.app import create_app
from src.models import Account, db as _db


@pytest.fixture(scope="function")
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def default_account(app):
    """Create a default account for testing."""
    with app.app_context():
        account = Account(name="Test Account")
        _db.session.add(account)
        _db.session.commit()
        return account.id


@pytest.fixture
def sample_trade_data(default_account):
    """Sample trade data for testing."""
    return {
        "account_id": default_account,
        "symbol": "BTCUSDT",
        "direction": "long",
        "entry_price": 67234.50,
        "stop_loss": 66800.00,
        "position_size": 0.1,
        "notes": "Test trade",
    }


@pytest.fixture
def sample_closed_trade_data(default_account):
    """Sample trade data with take_profit for closed trade testing."""
    return {
        "account_id": default_account,
        "symbol": "BTCUSDT",
        "direction": "long",
        "entry_price": 67234.50,
        "stop_loss": 66800.00,
        "take_profit": 68500.00,
        "position_size": 0.1,
        "notes": "Test trade",
    }

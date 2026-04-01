"""Test fixtures for TradeLogger."""

import pytest
from src.app import create_app
from src.models import Account, User, db as _db
from src.utils.jwt_utils import generate_access_token
from src.utils.password_utils import hash_password


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
def default_user(app):
    """Create a default user for testing."""
    with app.app_context():
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("TestPassword123!"),
            auth_provider="email",
        )
        _db.session.add(user)
        _db.session.commit()
        return user.id


@pytest.fixture
def auth_token(app, default_user):
    """Generate authentication token for default user."""
    with app.app_context():
        user = _db.session.get(User, default_user)
        token = generate_access_token(user.id, user.email)
        return token


@pytest.fixture
def auth_client(client, auth_token):
    """Create authenticated test client."""
    client.set_cookie("access_token", auth_token)
    return client


@pytest.fixture
def default_account(app, default_user):
    """Create a default account for testing."""
    with app.app_context():
        account = Account(name="Test Account", user_id=default_user)
        _db.session.add(account)
        _db.session.commit()
        return account.id


@pytest.fixture
def sample_trade_data(default_account, default_user):
    """Sample trade data for testing."""
    return {
        "user_id": default_user,
        "account_id": default_account,
        "symbol": "BTCUSDT",
        "direction": "long",
        "entry_price": 67234.50,
        "stop_loss": 66800.00,
        "position_size": 0.1,
        "notes": "Test trade",
    }


@pytest.fixture
def sample_closed_trade_data(default_account, default_user):
    """Sample trade data with take_profit for closed trade testing."""
    return {
        "user_id": default_user,
        "account_id": default_account,
        "symbol": "BTCUSDT",
        "direction": "long",
        "entry_price": 67234.50,
        "stop_loss": 66800.00,
        "take_profit": 68500.00,
        "position_size": 0.1,
        "notes": "Test trade",
    }

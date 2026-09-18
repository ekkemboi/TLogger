"""Price validation tests for TradeLogger API.

Tests validation guardrails for:
- LONG trades: TP must be > entry, SL must be < entry
- SHORT trades: TP must be < entry, SL must be > entry
"""

import json
import pytest
from src.app import create_app
from src.models import Account, FavoriteProduct, User, db as _db


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
        user = User(email="test@example.com", name="Test User")
        _db.session.add(user)
        _db.session.commit()
        return user.id


@pytest.fixture
def default_account(app, default_user):
    """Create a default account for testing."""
    with app.app_context():
        account = Account(name="Test Account", user_id=default_user)
        _db.session.add(account)
        _db.session.commit()
        return account.id


@pytest.fixture
def favorite_product(app, default_user):
    """Create a favorite product for testing."""
    with app.app_context():
        fav = FavoriteProduct(
            symbol="BTCUSDT",
            point_value=1,
            fees=5.0,
            user_id=default_user,
        )
        _db.session.add(fav)
        _db.session.commit()
        return fav.symbol


def make_trade_payload(
    account_id,
    symbol,
    direction,
    entry_price,
    user_id=None,
    stop_loss=None,
    take_profit=None,
    position_size=0.1,
):
    """Helper to create trade payload."""
    payload = {
        "account_id": account_id,
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "position_size": position_size,
    }
    if user_id is not None:
        payload["user_id"] = user_id
    if stop_loss is not None:
        payload["stop_loss"] = stop_loss
    if take_profit is not None:
        payload["take_profit"] = take_profit
    return payload


class TestLongTradePriceValidation:
    """Tests for LONG trade price validation rules."""

    def test_long_tp_less_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade with TP < entry should fail validation."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=49000,  # TP < entry - invalid
            stop_loss=49000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            "higher" in data["error"].lower() or "take profit" in data["error"].lower()
        )

    def test_long_sl_greater_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade with SL > entry should fail validation."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            stop_loss=51000,  # SL > entry - invalid
            take_profit=51000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "lower" in data["error"].lower() or "stop loss" in data["error"].lower()

    def test_long_valid_tp_and_sl_passes(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade with valid TP > entry AND SL < entry should pass."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=51000,  # TP > entry - valid
            stop_loss=49000,  # SL < entry - valid
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert float(data["take_profit"]) == 51000
        assert float(data["stop_loss"]) == 49000

    def test_long_tp_equal_to_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade with TP = entry should fail (must be greater)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=50000,  # TP = entry - invalid (must be greater)
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_long_sl_equal_to_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade with SL = entry should fail (must be less)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            stop_loss=50000,  # SL = entry - invalid (must be less)
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestShortTradePriceValidation:
    """Tests for SHORT trade price validation rules."""

    def test_short_tp_greater_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade with TP > entry should fail validation."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            take_profit=51000,  # TP > entry - invalid
            stop_loss=49000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            "lower" in data["error"].lower() or "take profit" in data["error"].lower()
        )

    def test_short_sl_less_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade with SL < entry should fail validation."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            stop_loss=49000,  # SL < entry - invalid
            take_profit=49000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "higher" in data["error"].lower() or "stop loss" in data["error"].lower()

    def test_short_valid_tp_and_sl_passes(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade with valid TP < entry AND SL > entry should pass."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            take_profit=49000,  # TP < entry - valid
            stop_loss=51000,  # SL > entry - valid
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert float(data["take_profit"]) == 49000
        assert float(data["stop_loss"]) == 51000

    def test_short_tp_equal_to_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade with TP = entry should fail (must be less)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            take_profit=50000,  # TP = entry - invalid (must be less)
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_short_sl_equal_to_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade with SL = entry should fail (must be greater)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            stop_loss=50000,  # SL = entry - invalid (must be greater)
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestOptionalFieldsValidation:
    """Tests for optional TP/SL fields."""

    def test_long_missing_tp_allowed(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade without TP should be allowed (optional field)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            stop_loss=49000,  # SL < entry - valid
            take_profit=None,  # Missing TP - should be allowed
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed (TP is optional)
        assert response.status_code == 201

    def test_long_missing_sl_allowed(
        self, client, default_account, default_user, favorite_product
    ):
        """LONG trade without SL should be allowed (optional field)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=51000,  # TP > entry - valid
            stop_loss=None,  # Missing SL - should be allowed
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed (SL is optional)
        assert response.status_code == 201

    def test_short_missing_tp_allowed(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade without TP should be allowed (optional field)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            stop_loss=51000,  # SL > entry - valid
            take_profit=None,  # Missing TP - should be allowed
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed (TP is optional)
        assert response.status_code == 201

    def test_short_missing_sl_allowed(
        self, client, default_account, default_user, favorite_product
    ):
        """SHORT trade without SL should be allowed (optional field)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            take_profit=49000,  # TP < entry - valid
            stop_loss=None,  # Missing SL - should be allowed
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed (SL is optional)
        assert response.status_code == 201

    def test_both_missing_tp_sl_allowed(
        self, client, default_account, default_user, favorite_product
    ):
        """Trade without both TP and SL should be allowed (both optional)."""
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=None,
            stop_loss=None,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should succeed (both are optional)
        assert response.status_code == 201


class TestUpdateTradePriceValidation:
    """Tests for price validation on PUT /trades/<id> endpoint."""

    def test_update_long_tp_to_less_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """Updating LONG trade TP to < entry should fail."""
        # First create a valid trade
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="long",
            entry_price=50000,
            take_profit=51000,
            stop_loss=49000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        trade_id = response.get_json()["id"]

        # Try to update TP to invalid value
        update_payload = {"take_profit": 49000}  # TP < entry - invalid

        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_update_short_tp_to_greater_than_entry_fails(
        self, client, default_account, default_user, favorite_product
    ):
        """Updating SHORT trade TP to > entry should fail."""
        # First create a valid trade
        payload = make_trade_payload(
            account_id=default_account,
            user_id=default_user,
            symbol=favorite_product,
            direction="short",
            entry_price=50000,
            take_profit=49000,
            stop_loss=51000,
        )

        response = client.post(
            "/api/trades",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        trade_id = response.get_json()["id"]

        # Try to update TP to invalid value
        update_payload = {"take_profit": 51000}  # TP > entry - invalid

        response = client.put(
            f"/api/trades/{trade_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

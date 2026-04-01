"""Tests for account API endpoints."""

import json
import pytest


class TestAccountCRUD:
    """Tests for account CRUD operations."""

    def test_create_account_success(self, auth_client):
        """Test creating an account successfully."""
        response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Main Trading Account"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Main Trading Account"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_account_missing_name(self, auth_client):
        """Test creating account without name fails."""
        response = auth_client.post(
            "/api/accounts",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_account_unauthenticated(self, client):
        """Test creating account without authentication fails."""
        response = client.post(
            "/api/accounts",
            data=json.dumps({"name": "Test Account"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_get_accounts_empty(self, auth_client):
        """Test getting accounts when none exist."""
        response = auth_client.get("/api/accounts")
        assert response.status_code == 200
        data = response.get_json()
        assert data["accounts"] == []
        assert data["total"] == 0

    def test_get_accounts_with_data(self, auth_client):
        """Test getting accounts after creating one."""
        auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Account 1"}),
            content_type="application/json",
        )
        auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Account 2"}),
            content_type="application/json",
        )
        response = auth_client.get("/api/accounts")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["accounts"]) == 2
        assert data["total"] == 2

    def test_get_accounts_unauthenticated(self, client):
        """Test getting accounts without authentication fails."""
        response = client.get("/api/accounts")
        assert response.status_code == 401

    def test_get_account_success(self, auth_client):
        """Test getting a single account."""
        create_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Test Account"}),
            content_type="application/json",
        )
        account_id = create_response.get_json()["id"]

        response = auth_client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == account_id
        assert data["name"] == "Test Account"

    def test_get_account_not_found(self, auth_client):
        """Test getting non-existent account."""
        response = auth_client.get("/api/accounts/nonexistent-id")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_get_account_wrong_user(self, auth_client, app, default_user):
        """Test getting account belonging to different user fails."""
        from src.models import Account, User, db
        from src.utils.password_utils import hash_password
        from src.utils.jwt_utils import generate_access_token

        # Create another user and their account
        with app.app_context():
            other_user = User(
                email="other@example.com",
                name="Other User",
                password_hash=hash_password("OtherPass123!"),
                auth_provider="email",
            )
            db.session.add(other_user)
            db.session.commit()

            other_account = Account(name="Other Account", user_id=other_user.id)
            db.session.add(other_account)
            db.session.commit()
            other_account_id = other_account.id

        # Try to access other user's account
        response = auth_client.get(f"/api/accounts/{other_account_id}")
        assert response.status_code == 404  # Should not reveal existence

    def test_update_account_success(self, auth_client):
        """Test updating an account."""
        create_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Original Name"}),
            content_type="application/json",
        )
        account_id = create_response.get_json()["id"]

        response = auth_client.put(
            f"/api/accounts/{account_id}",
            data=json.dumps({"name": "Updated Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Updated Name"

    def test_update_account_not_found(self, auth_client):
        """Test updating non-existent account."""
        response = auth_client.put(
            "/api/accounts/nonexistent-id",
            data=json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_delete_account_success(self, auth_client):
        """Test soft deleting an account."""
        create_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "To Delete"}),
            content_type="application/json",
        )
        account_id = create_response.get_json()["id"]

        response = auth_client.delete(f"/api/accounts/{account_id}")
        assert response.status_code == 200

        # Verify soft delete - account should still exist but be inactive
        # But won't show in list since we filter by is_active
        get_response = auth_client.get(f"/api/accounts/{account_id}")
        assert get_response.status_code == 200
        data = get_response.get_json()
        assert data["is_active"] is False

    def test_delete_account_not_found(self, auth_client):
        """Test deleting non-existent account."""
        response = auth_client.delete("/api/accounts/nonexistent-id")
        assert response.status_code == 404


class TestAccountTrades:
    """Tests for nested account trades routes."""

    def test_get_trades_for_account_empty(self, auth_client):
        """Test getting trades for account with no trades."""
        create_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Empty Account"}),
            content_type="application/json",
        )
        account_id = create_response.get_json()["id"]

        response = auth_client.get(f"/api/accounts/{account_id}/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert data["trades"] == []
        assert data["total"] == 0

    def test_get_trades_for_account_with_data(self, auth_client, sample_trade_data):
        """Test getting trades for account with trades."""
        # Create account
        account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Trading Account"}),
            content_type="application/json",
        )
        account_id = account_response.get_json()["id"]

        # Create trade with account_id
        trade_data = {**sample_trade_data, "account_id": account_id}
        auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )

        response = auth_client.get(f"/api/accounts/{account_id}/trades")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"

    def test_get_trades_for_account_not_found(self, auth_client):
        """Test getting trades for non-existent account."""
        response = auth_client.get("/api/accounts/nonexistent-id/trades")
        assert response.status_code == 404


class TestTradeAccountRequired:
    """Tests for account_id requirement on trades."""

    def test_create_trade_requires_account_id(self, auth_client, sample_trade_data):
        """Test creating trade without account_id fails."""
        # Remove account_id from sample data
        trade_data = {k: v for k, v in sample_trade_data.items() if k != "account_id"}
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "account_id" in data["error"].lower()

    def test_create_trade_with_account_success(self, auth_client, sample_trade_data):
        """Test creating trade with valid account_id succeeds."""
        # Create account first
        account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Test Account"}),
            content_type="application/json",
        )
        account_id = account_response.get_json()["id"]

        # Create trade with account_id
        trade_data = {**sample_trade_data, "account_id": account_id}
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["account_id"] == account_id

    def test_create_trade_invalid_account_id(self, auth_client, sample_trade_data):
        """Test creating trade with invalid account_id fails."""
        trade_data = {**sample_trade_data, "account_id": "invalid-account-id"}
        response = auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestBulkAssign:
    """Tests for bulk assigning trades to accounts."""

    def test_bulk_assign_success(self, auth_client, sample_trade_data):
        """Test bulk assigning trades to account."""
        # Create account
        account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Bulk Account"}),
            content_type="application/json",
        )
        account_id = account_response.get_json()["id"]

        # Create trades
        trade_ids = []
        for i in range(3):
            trade_data = {
                **sample_trade_data,
                "symbol": f"TEST{i}USDT",
                "account_id": account_id,
            }
            trade_response = auth_client.post(
                "/api/trades",
                data=json.dumps(trade_data),
                content_type="application/json",
            )
            trade_ids.append(trade_response.get_json()["id"])

        # Create a new account to reassign to
        new_account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "New Account"}),
            content_type="application/json",
        )
        new_account_id = new_account_response.get_json()["id"]

        # Bulk assign
        response = auth_client.post(
            "/api/accounts/bulk-assign",
            data=json.dumps({"account_id": new_account_id, "trade_ids": trade_ids}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["assigned_count"] == 3

        # Verify trades are now in new account
        trades_response = auth_client.get(f"/api/accounts/{new_account_id}/trades")
        assert trades_response.status_code == 200
        assert len(trades_response.get_json()["trades"]) == 3

    def test_bulk_assign_partial_success(self, auth_client, sample_trade_data):
        """Test bulk assigning with some invalid trade IDs."""
        # Create account
        account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Partial Account"}),
            content_type="application/json",
        )
        account_id = account_response.get_json()["id"]

        # Create one valid trade
        trade_data = {**sample_trade_data, "account_id": account_id}
        trade_response = auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        valid_trade_id = trade_response.get_json()["id"]

        # Try to assign valid and invalid trades
        response = auth_client.post(
            "/api/accounts/bulk-assign",
            data=json.dumps(
                {
                    "account_id": account_id,
                    "trade_ids": [valid_trade_id, "invalid-id-1", "invalid-id-2"],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 207  # Partial success
        data = response.get_json()
        assert data["assigned_count"] == 1
        assert len(data["failed_ids"]) == 2

    def test_bulk_assign_invalid_account(self, auth_client, sample_trade_data):
        """Test bulk assigning to non-existent account."""
        # Create a trade first
        account_response = auth_client.post(
            "/api/accounts",
            data=json.dumps({"name": "Temp Account"}),
            content_type="application/json",
        )
        account_id = account_response.get_json()["id"]

        trade_data = {**sample_trade_data, "account_id": account_id}
        trade_response = auth_client.post(
            "/api/trades",
            data=json.dumps(trade_data),
            content_type="application/json",
        )
        trade_id = trade_response.get_json()["id"]

        # Try to assign to non-existent account
        response = auth_client.post(
            "/api/accounts/bulk-assign",
            data=json.dumps(
                {"account_id": "nonexistent-account-id", "trade_ids": [trade_id]}
            ),
            content_type="application/json",
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

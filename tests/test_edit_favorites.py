"""Tests for edit favorites API endpoints."""

import json
import pytest


class TestEditFavorite:
    """Tests for editing favorites via PUT /api/favorites/<id>."""

    def test_update_favorite_symbol(self, client):
        """Update favorite symbol."""
        # Create a favorite first
        create_response = client.post(
            "/api/favorites",
            data=json.dumps({"symbol": "BTCUSDT", "point_value": 1, "fees": 0}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        favorite_id = create_response.get_json()["id"]

        # Update the symbol
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"symbol": "ETHUSDT"}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["symbol"] == "ETHUSDT"
        assert data["id"] == favorite_id

    def test_update_favorite_point_value(self, client):
        """Update point value."""
        # Create a favorite first
        create_response = client.post(
            "/api/favorites",
            data=json.dumps({"symbol": "BTCUSDT", "point_value": 1, "fees": 0}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        favorite_id = create_response.get_json()["id"]

        # Update point value
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"point_value": 10}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["point_value"] == 10

    def test_update_favorite_fees(self, client):
        """Update fees."""
        # Create a favorite first
        create_response = client.post(
            "/api/favorites",
            data=json.dumps({"symbol": "BTCUSDT", "point_value": 1, "fees": 0}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        favorite_id = create_response.get_json()["id"]

        # Update fees
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"fees": 5.5}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["fees"] == 5.5

    def test_update_favorite_is_active(self, client):
        """Toggle is_active status."""
        # Create a favorite first
        create_response = client.post(
            "/api/favorites",
            data=json.dumps({"symbol": "BTCUSDT", "point_value": 1, "fees": 0}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        favorite_id = create_response.get_json()["id"]

        # Verify it's active initially
        assert create_response.get_json()["is_active"] is True

        # Deactivate
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"is_active": False}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["is_active"] is False

        # Reactivate
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"is_active": True}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["is_active"] is True

    def test_update_nonexistent_favorite(self, client):
        """Updating non-existent returns 404."""
        response = client.put(
            "/api/favorites/nonexistent-id",
            data=json.dumps({"symbol": "ETHUSDT"}),
            content_type="application/json",
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_update_favorite_multiple_fields(self, client):
        """Update multiple fields at once."""
        # Create a favorite first
        create_response = client.post(
            "/api/favorites",
            data=json.dumps({"symbol": "BTCUSDT", "point_value": 1, "fees": 0}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        favorite_id = create_response.get_json()["id"]

        # Update multiple fields
        update_response = client.put(
            f"/api/favorites/{favorite_id}",
            data=json.dumps({"symbol": "SOLUSDT", "point_value": 5, "fees": 2.5}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        data = update_response.get_json()
        assert data["symbol"] == "SOLUSDT"
        assert data["point_value"] == 5
        assert data["fees"] == 2.5

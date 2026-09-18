"""Tests for broker sync service."""

import json

import pytest
from src.models import BrokerConnection, db


class TestBrokerConnectionModel:
    """Tests for BrokerConnection model."""

    def test_create_connection(self, app, default_user):
        with app.app_context():
            conn = BrokerConnection(
                user_id=default_user,
                broker="tradovate",
                label="My Tradovate Account",
                api_key="encrypted-key-123",
                account_id="demo-123",
                is_active=True,
                sync_interval=60,
            )
            db.session.add(conn)
            db.session.commit()

            saved = BrokerConnection.query.filter_by(user_id=default_user, broker="tradovate").first()
            assert saved is not None
            assert saved.label == "My Tradovate Account"
            assert saved.is_active is True

    def test_connection_defaults(self, app, default_user):
        with app.app_context():
            conn = BrokerConnection(
                user_id=default_user,
                broker="ctrader",
                label="cTrader Demo",
            )
            db.session.add(conn)
            db.session.commit()

            assert conn.is_active is True
            assert conn.sync_interval == 60
            assert conn.last_sync_at is None

    def test_multiple_connections_per_user(self, app, default_user):
        with app.app_context():
            conns = [
                BrokerConnection(user_id=default_user, broker="tradovate", label="Tradovate 1"),
                BrokerConnection(user_id=default_user, broker="tradovate", label="Tradovate 2"),
                BrokerConnection(user_id=default_user, broker="ctrader", label="cTrader"),
            ]
            db.session.add_all(conns)
            db.session.commit()

            user_conns = BrokerConnection.query.filter_by(user_id=default_user).all()
            assert len(user_conns) == 3

    def test_connection_user_isolation(self, app, default_user):
        with app.app_context():
            c1 = BrokerConnection(user_id=default_user, broker="tradovate", label="Mine")
            c2 = BrokerConnection(user_id="other-user", broker="tradovate", label="Theirs")
            db.session.add_all([c1, c2])
            db.session.commit()

            mine = BrokerConnection.query.filter_by(user_id=default_user).all()
            assert len(mine) == 1

    def test_connection_to_dict(self, app, default_user):
        with app.app_context():
            conn = BrokerConnection(
                user_id=default_user, broker="tradovate", label="Test",
                account_id="acc-123",
            )
            db.session.add(conn)
            db.session.commit()

            d = conn.to_dict()
            assert d["broker"] == "tradovate"
            assert d["label"] == "Test"
            assert d["account_id"] == "acc-123"
            assert "api_key" not in d


class TestBrokerSyncAPI:
    """Tests for broker sync API endpoints."""

    BROKERS_URL = "/api/brokers"

    def test_list_connections_empty(self, auth_client):
        response = auth_client.get(self.BROKERS_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert data["connections"] == []

    def test_create_connection(self, auth_client):
        payload = {
            "broker": "tradovate",
            "label": "My Tradovate",
            "api_key": "demo-key",
            "api_secret": "demo-secret",
            "account_id": "acc-001",
        }
        response = auth_client.post(
            self.BROKERS_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["broker"] == "tradovate"
        assert data["label"] == "My Tradovate"

    def test_create_connection_missing_fields(self, auth_client):
        response = auth_client.post(
            self.BROKERS_URL,
            data=json.dumps({"broker": "tradovate"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_connection_unauthenticated(self, client):
        response = client.post(
            self.BROKERS_URL,
            data=json.dumps({"broker": "tradovate", "label": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_update_connection(self, auth_client, app, default_user):
        with app.app_context():
            conn = BrokerConnection(user_id=default_user, broker="tradovate", label="Old Label")
            db.session.add(conn)
            db.session.commit()
            conn_id = conn.id

        response = auth_client.put(
            f"{self.BROKERS_URL}/{conn_id}",
            data=json.dumps({"label": "New Label"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["label"] == "New Label"

    def test_delete_connection(self, auth_client, app, default_user):
        with app.app_context():
            conn = BrokerConnection(user_id=default_user, broker="ctrader", label="To Delete")
            db.session.add(conn)
            db.session.commit()
            conn_id = conn.id

        response = auth_client.delete(f"{self.BROKERS_URL}/{conn_id}")
        assert response.status_code == 200

        with app.app_context():
            deleted = BrokerConnection.query.get(conn_id)
            assert deleted is None

    def test_trigger_sync(self, auth_client, app, default_user):
        with app.app_context():
            conn = BrokerConnection(user_id=default_user, broker="tradovate", label="Sync Test")
            db.session.add(conn)
            db.session.commit()
            conn_id = conn.id

        response = auth_client.post(f"{self.BROKERS_URL}/{conn_id}/sync")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data

    def test_get_sync_status(self, auth_client, app, default_user):
        with app.app_context():
            conn = BrokerConnection(user_id=default_user, broker="tradovate", label="Status Test")
            db.session.add(conn)
            db.session.commit()
            conn_id = conn.id

        response = auth_client.get(f"{self.BROKERS_URL}/{conn_id}/sync-status")
        assert response.status_code == 200

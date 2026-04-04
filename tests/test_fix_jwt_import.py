"""Test for desktop authentication flow via direct redirect."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as jwt_lib
import pytest

from src.models import User
from src.utils.jwt_utils import generate_access_token


class TestDesktopAuthFlow:
    """Test desktop authentication via direct redirect from login."""

    def test_login_desktop_redirect(self, client, default_user):
        """Test login with source=desktop redirects to tradelogger:// protocol."""
        with client.application.app_context():
            user = User.query.get(default_user)

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": user.email,
                    "password": "TestPassword123!",  # Default test password from conftest.py
                    "source": "desktop",
                    "remember_me": True,
                }
            ),
            content_type="application/json",
        )

        # Should redirect to tradelogger:// protocol
        assert response.status_code == 302
        assert "tradelogger://auth?status=success" in response.location
        assert "access_token=" in response.location
        assert "refresh_token=" in response.location
        assert "remember_me=true" in response.location

    def test_login_web_returns_json(self, client, default_user):
        """Test login without source returns JSON (web flow)."""
        with client.application.app_context():
            user = User.query.get(default_user)

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": user.email,
                    "password": "TestPassword123!",
                }
            ),
            content_type="application/json",
        )

        # Should return JSON response
        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data)
        assert "message" in data
        assert "user" in data

    def test_login_desktop_invalid_credentials(self, client):
        """Test desktop login with invalid credentials returns error (not redirect)."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": "wrong@example.com",
                    "password": "wrongpassword",
                    "source": "desktop",
                }
            ),
            content_type="application/json",
        )

        # Should return 401 error, not redirect
        assert response.status_code == 401
        assert response.content_type == "application/json"

    def test_auth_status_with_bearer_token(self, client, default_user):
        """Test auth status accepts Authorization: Bearer header."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        response = client.get(
            "/api/auth/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is True
        assert data["user"]["email"] == user.email

    def test_refresh_token_with_bearer(self, client, default_user, app):
        """Test token refresh accepts Authorization: Bearer header."""
        from src.utils.jwt_utils import generate_refresh_token

        with app.app_context():
            user = User.query.get(default_user)
            refresh_token = generate_refresh_token(user.id)

        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data
        assert "refresh_token" in data

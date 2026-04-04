"""Test for desktop auth callback jwt import fix."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as jwt_lib
import pytest

from src.models import User
from src.utils.jwt_utils import generate_access_token


class TestDesktopAuthCallback:
    """Test desktop authentication callback endpoint."""

    def test_desktop_callback_success(self, client, default_user):
        """Test successful desktop auth callback redirects with success status."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        client.set_cookie("access_token", access_token)

        response = client.get("/api/auth/desktop-callback")

        # Should redirect to tradelogger:// protocol
        assert response.status_code == 302
        assert "tradelogger://auth?status=success" in response.location

    def test_desktop_callback_no_token(self, client):
        """Test desktop callback without token redirects as unauthenticated."""
        response = client.get("/api/auth/desktop-callback")

        assert response.status_code == 302
        assert "tradelogger://auth?status=unauthenticated" in response.location

    def test_desktop_callback_expired_token(self, client, default_user, app):
        """Test desktop callback with expired token redirects with expired status.

        Bug: jwt import was missing causing NameError on jwt.ExpiredSignatureError
        """
        # Create an expired token manually
        with app.app_context():
            user = User.query.get(default_user)
            payload = {
                "sub": user.id,
                "email": user.email,
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            }
            expired_token = jwt_lib.encode(
                payload,
                app.config["JWT_SECRET_KEY"],
                algorithm="HS256",
            )

        client.set_cookie("access_token", expired_token)

        response = client.get("/api/auth/desktop-callback")

        # Should redirect with expired status, not 500 error
        assert response.status_code == 302
        assert "tradelogger://auth?status=expired" in response.location

    def test_desktop_callback_invalid_token(self, client):
        """Test desktop callback with invalid token redirects with invalid status.

        Bug: jwt import was missing causing NameError on jwt.InvalidTokenError
        """
        client.set_cookie("access_token", "invalid.token.format")

        response = client.get("/api/auth/desktop-callback")

        # Should redirect with invalid status, not 500 error
        assert response.status_code == 302
        assert "tradelogger://auth?status=invalid" in response.location

    def test_desktop_callback_malformed_token(self, client):
        """Test desktop callback with malformed token redirects with invalid status."""
        client.set_cookie("access_token", "not-a-valid-jwt")

        response = client.get("/api/auth/desktop-callback")

        # Should redirect with invalid status
        assert response.status_code == 302
        assert "tradelogger://auth?status=invalid" in response.location

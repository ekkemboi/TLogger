"""Tests for OAuth 2.0 routes with PKCE support."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestOAuthAuthorize:
    """Test OAuth authorization endpoint."""

    def test_authorize_requires_redirect_uri(self, client):
        """Test that authorize requires redirect_uri."""
        response = client.get(
            "/api/oauth/authorize?code_challenge=challenge123&response_type=code"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "redirect_uri is required" in data["error"]

    def test_authorize_requires_code_challenge(self, client):
        """Test that authorize requires code_challenge."""
        response = client.get(
            "/api/oauth/authorize?redirect_uri=tradelogger://auth&response_type=code"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "code_challenge is required" in data["error"]

    def test_authorize_requires_response_type(self, client):
        """Test that authorize requires response_type=code."""
        response = client.get(
            "/api/oauth/authorize?redirect_uri=tradelogger://auth&code_challenge=challenge123"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "response_type must be 'code'" in data["error"]

    def test_authorize_success(self, client):
        """Test successful authorization request."""
        response = client.get(
            "/api/oauth/authorize?"
            + "redirect_uri=tradelogger://auth&"
            + "code_challenge=challenge123&"
            + "state=state456&"
            + "response_type=code"
        )

        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location
        assert "oauth_flow=true" in response.location

    def test_authorize_with_fallback_uri(self, client):
        """Test authorization with fallback URI."""
        response = client.get(
            "/api/oauth/authorize?"
            + "redirect_uri=tradelogger://auth&"
            + "fallback_uri=http://127.0.0.1:45678/callback&"
            + "code_challenge=challenge123&"
            + "response_type=code"
        )

        assert response.status_code == 302  # Redirect to login

    def test_authorize_stores_session_data(self, client):
        """Test that authorize stores OAuth data in session."""
        with client.session_transaction() as session:
            session.clear()

        client.get(
            "/api/oauth/authorize?"
            + "redirect_uri=tradelogger://auth&"
            + "code_challenge=challenge123&"
            + "state=state456&"
            + "response_type=code"
        )

        with client.session_transaction() as session:
            assert session["oauth_redirect_uri"] == "tradelogger://auth"
            assert session["oauth_code_challenge"] == "challenge123"
            assert session["oauth_state"] == "state456"
            assert session["oauth_source"] == "desktop"


class TestOAuthCallback:
    """Test OAuth callback endpoint."""

    def test_callback_requires_token(self, client):
        """Test that callback requires authentication token."""
        response = client.get("/api/oauth/callback")

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Authentication required" in data["error"]

    def test_callback_with_invalid_token(self, client):
        """Test callback with invalid token."""
        response = client.get("/api/oauth/callback?token=invalid")

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Invalid or expired token" in data["error"]

    @patch("src.utils.jwt_utils.verify_access_token")
    @patch("src.services.auth_service.get_user_by_id")
    def test_callback_success(self, mock_get_user, mock_verify_token, client):
        """Test successful OAuth callback."""
        # Setup mocks
        mock_verify_token.return_value = {"sub": "user-123"}
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user

        # Setup session
        with client.session_transaction() as session:
            session["oauth_redirect_uri"] = "tradelogger://auth"
            session["oauth_code_challenge"] = "challenge123"
            session["oauth_state"] = "state456"

        response = client.get("/api/oauth/callback?token=valid&state=state456")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "redirect_url" in data
        assert "tradelogger://auth" in data["redirect_url"]
        assert "code=" in data["redirect_url"]

    @patch("src.utils.jwt_utils.verify_access_token")
    @patch("src.services.auth_service.get_user_by_id")
    def test_callback_state_mismatch(self, mock_get_user, mock_verify_token, client):
        """Test callback fails on state mismatch."""
        mock_verify_token.return_value = {"sub": "user-123"}
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user

        with client.session_transaction() as session:
            session["oauth_redirect_uri"] = "tradelogger://auth"
            session["oauth_code_challenge"] = "challenge123"
            session["oauth_state"] = "state456"

        response = client.get("/api/oauth/callback?token=valid&state=wrong_state")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid state parameter" in data["error"]

    @patch("src.utils.jwt_utils.verify_access_token")
    def test_callback_expired_session(self, mock_verify_token, client):
        """Test callback fails when OAuth session expired."""
        mock_verify_token.return_value = {"sub": "user-123"}

        # No session data set
        response = client.get("/api/oauth/callback?token=valid")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "OAuth session expired" in data["error"]


class TestOAuthToken:
    """Test OAuth token exchange endpoint."""

    def test_token_requires_grant_type(self, client):
        """Test that token requires grant_type."""
        response = client.post(
            "/api/oauth/token",
            json={"code": "abc123", "code_verifier": "verifier"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Unsupported grant_type" in data["error"]

    def test_token_requires_code(self, client):
        """Test that token requires code."""
        response = client.post(
            "/api/oauth/token",
            json={"code_verifier": "verifier", "grant_type": "authorization_code"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "code and code_verifier are required" in data["error"]

    def test_token_requires_code_verifier(self, client):
        """Test that token requires code_verifier."""
        response = client.post(
            "/api/oauth/token",
            json={"code": "abc123", "grant_type": "authorization_code"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "code and code_verifier are required" in data["error"]

    @patch("src.routes.oauth.oauth_service")
    @patch("src.routes.oauth.auth_service")
    @patch("src.routes.oauth.generate_access_token")
    @patch("src.routes.oauth.generate_refresh_token")
    def test_token_exchange_success(
        self, mock_refresh, mock_access, mock_auth_service, mock_oauth_service, client
    ):
        """Test successful token exchange."""
        # Setup mocks
        mock_auth_code = MagicMock()
        mock_auth_code.user_id = "user-123"
        mock_auth_code.used = False
        mock_oauth_service.exchange_code.return_value = mock_auth_code

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_auth_service.get_user_by_id.return_value = mock_user

        mock_access.return_value = "access-token-123"
        mock_refresh.return_value = "refresh-token-456"

        response = client.post(
            "/api/oauth/token",
            json={
                "code": "auth-code-abc",
                "code_verifier": "verifier-xyz",
                "grant_type": "authorization_code",
            },
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["access_token"] == "access-token-123"
        assert data["refresh_token"] == "refresh-token-456"
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600

    @patch("src.routes.oauth.oauth_service")
    def test_token_invalid_code(self, mock_oauth_service, client):
        """Test token exchange fails with invalid code."""
        mock_oauth_service.exchange_code.return_value = None

        response = client.post(
            "/api/oauth/token",
            json={
                "code": "invalid-code",
                "code_verifier": "verifier",
                "grant_type": "authorization_code",
            },
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Invalid or expired authorization code" in data["error"]

    @patch("src.routes.oauth.oauth_service")
    @patch("src.services.auth_service.get_user_by_id")
    def test_token_user_not_found(self, mock_get_user, mock_oauth_service, client):
        """Test token exchange fails when user not found."""
        mock_auth_code = MagicMock()
        mock_auth_code.user_id = "user-123"
        mock_oauth_service.exchange_code.return_value = mock_auth_code
        mock_get_user.return_value = None

        response = client.post(
            "/api/oauth/token",
            json={
                "code": "auth-code",
                "code_verifier": "verifier",
                "grant_type": "authorization_code",
            },
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "User not found" in data["error"]


class TestOAuthPKCE:
    """Test OAuth PKCE helper endpoint."""

    def test_generate_pkce_success(self, client):
        """Test successful PKCE generation."""
        response = client.get("/api/oauth/pkce")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "code_verifier" in data
        assert "code_challenge" in data
        assert "method" in data
        assert data["method"] == "S256"
        assert len(data["code_verifier"]) > 0
        assert len(data["code_challenge"]) > 0

    def test_generate_pkce_unique(self, client):
        """Test that generated PKCE pairs are unique."""
        verifiers = set()
        challenges = set()

        for _ in range(5):
            response = client.get("/api/oauth/pkce")
            data = json.loads(response.data)
            verifiers.add(data["code_verifier"])
            challenges.add(data["code_challenge"])

        assert len(verifiers) == 5
        assert len(challenges) == 5

    def test_generate_pkce_verifier_format(self, client):
        """Test that code verifier uses base64url encoding."""
        response = client.get("/api/oauth/pkce")
        data = json.loads(response.data)
        verifier = data["code_verifier"]

        # Base64url should not contain +, /, or trailing =
        assert "+" not in verifier
        assert "/" not in verifier
        assert "=" not in verifier

    def test_generate_pkce_challenge_is_hash(self, client):
        """Test that code challenge is SHA256 hash of verifier."""
        import base64
        import hashlib

        response = client.get("/api/oauth/pkce")
        data = json.loads(response.data)
        verifier = data["code_verifier"]
        challenge = data["code_challenge"]

        # Compute expected challenge
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
            .decode("ascii")
            .rstrip("=")
        )

        assert challenge == expected

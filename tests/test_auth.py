"""Tests for authentication endpoints."""

import json

import pytest

from src.models import User, db
from src.utils.jwt_utils import generate_access_token, generate_refresh_token
from src.utils.password_utils import hash_password, verify_password


class TestPasswordUtils:
    """Test password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing creates different hashes."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts should produce different hashes
        assert hash1.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False


class TestRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["message"] == "User registered successfully"
        assert response_data["user"]["email"] == "newuser@example.com"
        assert response_data["user"]["name"] == "New User"

        # Check cookies are set
        assert "access_token" in response.headers.get("Set-Cookie", "")

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        data = {"password": "SecurePass123!", "name": "New User"}
        response = client.post(
            "/api/auth/register",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "name": "New User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        data = {
            "email": "newuser@example.com",
            "password": "weak",
            "name": "New User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "password" in response_data["error"].lower()

    def test_register_duplicate_email(self, client, default_user):
        """Test registration with duplicate email."""
        # First, get the default user email
        with client.application.app_context():
            user = User.query.get(default_user)
            email = user.email

        data = {"email": email, "password": "SecurePass123!", "name": "New User"}
        response = client.post(
            "/api/auth/register",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "already registered" in response_data["error"].lower()

    def test_register_missing_body(self, client):
        """Test registration with no body."""
        response = client.post("/api/auth/register")

        # Flask returns 415 (Unsupported Media Type) when no content-type provided
        assert response.status_code in [400, 415]


class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, app):
        """Test successful login."""
        # Create a user with password
        with app.app_context():
            user = User(
                email="logintest@example.com",
                name="Login Test",
                password_hash=hash_password("SecurePass123!"),
                auth_provider="email",
            )
            db.session.add(user)
            db.session.commit()

        data = {"email": "logintest@example.com", "password": "SecurePass123!"}
        response = client.post(
            "/api/auth/login",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["message"] == "Login successful"
        assert response_data["user"]["email"] == "logintest@example.com"

        # Check cookies are set
        assert "access_token" in response.headers.get("Set-Cookie", "")

    def test_login_invalid_password(self, client, app):
        """Test login with invalid password."""
        # Create a user with password
        with app.app_context():
            user = User(
                email="logintest@example.com",
                name="Login Test",
                password_hash=hash_password("SecurePass123!"),
                auth_provider="email",
            )
            db.session.add(user)
            db.session.commit()

        data = {"email": "logintest@example.com", "password": "WrongPassword123!"}
        response = client.post(
            "/api/auth/login",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        data = {"email": "nonexistent@example.com", "password": "SecurePass123!"}
        response = client.post(
            "/api/auth/login",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        data = {"email": "test@example.com"}
        response = client.post(
            "/api/auth/login",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 401


class TestAuthStatus:
    """Test authentication status endpoint."""

    def test_auth_status_authenticated(self, client, default_user):
        """Test auth status when authenticated."""
        # Generate token for default user
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        # Set cookie
        client.set_cookie("access_token", access_token)

        response = client.get("/api/auth/status")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["authenticated"] is True
        assert response_data["user"]["id"] == default_user

    def test_auth_status_not_authenticated(self, client):
        """Test auth status when not authenticated."""
        response = client.get("/api/auth/status")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["authenticated"] is False
        assert response_data["user"] is None


class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_current_user_success(self, client, default_user):
        """Test getting current user info when authenticated."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        # Set cookie
        client.set_cookie("access_token", access_token)

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["id"] == default_user
        assert "email" in response_data
        assert "password_hash" not in response_data

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        client.set_cookie("access_token", "invalid-token")

        response = client.get("/api/auth/me")

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestRefreshToken:
    """Test token refresh endpoint."""

    def test_refresh_token_success(self, client, default_user):
        """Test successful token refresh."""
        with client.application.app_context():
            user = User.query.get(default_user)
            refresh_token = generate_refresh_token(user.id)

        client.set_cookie("refresh_token", refresh_token)

        response = client.post("/api/auth/refresh")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["message"] == "Token refreshed successfully"

        # Check new cookies are set
        assert "access_token" in response.headers.get("Set-Cookie", "")

    def test_refresh_token_missing(self, client):
        """Test refresh without token."""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        client.set_cookie("refresh_token", "invalid-token")

        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestLogout:
    """Test logout endpoint."""

    def test_logout_success(self, client, default_user):
        """Test successful logout."""
        # First login
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        client.set_cookie("access_token", access_token)

        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["message"] == "Logout successful"

        # Check cookies are cleared
        set_cookie_header = response.headers.get("Set-Cookie", "")
        assert (
            "access_token=;" in set_cookie_header
            or 'access_token=""' in set_cookie_header
        )


class TestGoogleOAuth:
    """Test Google OAuth endpoints."""

    def test_google_login_not_configured(self, client, app):
        """Test Google login when OAuth not configured."""
        with app.app_context():
            # Ensure no OAuth config
            app.config["GOOGLE_CLIENT_ID"] = None
            app.config["GOOGLE_CLIENT_SECRET"] = None

        response = client.get("/api/auth/google/login")

        assert response.status_code == 503
        response_data = json.loads(response.data)
        assert "not configured" in response_data["error"].lower()

    def test_google_callback_invalid_state(self, client):
        """Test Google callback with invalid state."""
        response = client.get("/api/auth/callback?state=invalid&code=test")

        # Should fail state validation
        assert response.status_code in [400, 503]


class TestJWTDecorator:
    """Test JWT decorator functionality."""

    def test_jwt_required_blocks_unauthenticated(self, client):
        """Test JWT decorator blocks requests without token."""
        # Try to access protected endpoint without auth
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_jwt_required_allows_authenticated(self, client, default_user):
        """Test JWT decorator allows authenticated requests."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        client.set_cookie("access_token", access_token)

        response = client.get("/api/auth/me")

        assert response.status_code == 200

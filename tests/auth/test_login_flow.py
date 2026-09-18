"""Unit tests for Login Flow user journey."""

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

        assert hash1 != hash2
        assert hash1.startswith("$2b$")

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


class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, app):
        """Test successful login."""
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

        assert "access_token" in response.headers.get("Set-Cookie", "")

    def test_login_invalid_password(self, client, app):
        """Test login with invalid password."""
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


class TestAuthStatus:
    """Test authentication status endpoint."""

    def test_auth_status_authenticated(self, client, default_user):
        """Test auth status when authenticated."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

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

        assert "access_token" in response.headers.get("Set-Cookie", "")

    def test_refresh_token_missing(self, client):
        """Test refresh without token."""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert "error" in response_data


class TestLogout:
    """Test logout endpoint."""

    def test_logout_success(self, client, default_user):
        """Test successful logout."""
        with client.application.app_context():
            user = User.query.get(default_user)
            access_token = generate_access_token(user.id, user.email)

        client.set_cookie("access_token", access_token)

        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["message"] == "Logout successful"

        set_cookie_header = response.headers.get("Set-Cookie", "")
        assert (
            "access_token=;" in set_cookie_header
            or 'access_token=""' in set_cookie_header
        )


class TestJWTDecorator:
    """Test JWT decorator functionality."""

    def test_jwt_required_blocks_unauthenticated(self, client):
        """Test JWT decorator blocks requests without token."""
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

"""JWT token utilities for authentication."""

from datetime import datetime, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def generate_access_token(user_id, email):
    """Generate a JWT access token.

    Args:
        user_id: The user's UUID
        email: The user's email address

    Returns:
        str: Encoded JWT access token
    """
    now = datetime.now(timezone.utc)
    expires = now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": expires,
    }

    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def generate_refresh_token(user_id):
    """Generate a JWT refresh token.

    Args:
        user_id: The user's UUID

    Returns:
        str: Encoded JWT refresh token
    """
    now = datetime.now(timezone.utc)
    expires = now + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]

    payload = {"sub": user_id, "type": "refresh", "iat": now, "exp": expires}

    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def verify_access_token(token):
    """Verify an access token and return the payload.

    Args:
        token: The JWT access token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_refresh_token(token):
    """Verify a refresh token and return the payload.

    Args:
        token: The JWT refresh token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def set_auth_cookies(response, access_token, refresh_token=None):
    """Set authentication cookies on the response.

    Args:
        response: Flask response object
        access_token: JWT access token
        refresh_token: JWT refresh token (optional)
    """
    secure = current_app.config.get("JWT_COOKIE_SECURE", False)
    samesite = current_app.config.get("JWT_COOKIE_SAMESITE", "Lax")

    # Set access token cookie (15 min expiry)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=900,  # 15 minutes
    )

    # Set refresh token cookie if provided (7 days expiry)
    if refresh_token:
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=604800,  # 7 days
        )


def clear_auth_cookies(response):
    """Clear authentication cookies.

    Args:
        response: Flask response object
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def jwt_required(f):
    """Decorator to require valid JWT access token.

    Args:
        f: The function to decorate

    Returns:
        function: Decorated function that checks for valid JWT
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        payload = verify_access_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Store user info in Flask g object for use in route
        g.current_user_id = payload["sub"]
        g.current_user_email = payload["email"]

        return f(*args, **kwargs)

    return decorated_function


def optional_jwt(f):
    """Decorator to optionally validate JWT access token.

    If token is present and valid, sets g.current_user_id and g.current_user_email.
    If token is missing or invalid, continues without setting these values.

    Args:
        f: The function to decorate

    Returns:
        function: Decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("access_token")
        g.current_user_id = None
        g.current_user_email = None

        if token:
            payload = verify_access_token(token)
            if payload:
                g.current_user_id = payload["sub"]
                g.current_user_email = payload["email"]

        return f(*args, **kwargs)

    return decorated_function

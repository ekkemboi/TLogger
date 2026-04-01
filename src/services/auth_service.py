"""Authentication service for user management."""

import re
import secrets

from src.models import User, db
from src.utils.password_utils import (
    hash_password,
    validate_password_strength,
    verify_password,
)


def validate_email(email):
    """Validate email format.

    Args:
        email: Email address string

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def register_user(email, password, name):
    """Register a new user with email and password.

    Args:
        email: User's email address
        password: User's plain text password
        name: User's display name

    Returns:
        tuple: (user: User or None, error: str or None)
    """
    # Validate email
    if not email or not validate_email(email):
        return None, "Valid email address is required"

    # Check if email already exists
    existing_user = User.query.filter_by(email=email.lower()).first()
    if existing_user:
        return None, "Email address already registered"

    # Validate password
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        return None, error

    # Validate name
    if not name or len(name.strip()) < 2:
        return None, "Name must be at least 2 characters long"

    # Create user
    user = User(
        email=email.lower().strip(),
        name=name.strip(),
        password_hash=hash_password(password),
        auth_provider="email",
    )

    db.session.add(user)
    db.session.commit()

    return user, None


def authenticate_user(email, password):
    """Authenticate a user with email and password.

    Args:
        email: User's email address
        password: User's plain text password

    Returns:
        tuple: (user: User or None, error: str or None)
    """
    if not email or not password:
        return None, "Email and password are required"

    # Find user by email
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return None, "Invalid email or password"

    # Check if user is active
    if not user.is_active:
        return None, "Account is deactivated"

    # Verify password
    if not user.password_hash:
        return None, "This account uses social login"

    if not verify_password(password, user.password_hash):
        return None, "Invalid email or password"

    return user, None


def get_or_create_google_user(google_id, email, name, profile_picture=None):
    """Get existing user or create new user from Google OAuth data.

    Args:
        google_id: Google's unique user ID
        email: User's email address
        name: User's display name
        profile_picture: URL to profile picture (optional)

    Returns:
        tuple: (user: User or None, error: str or None)
    """
    if not google_id or not email:
        return None, "Google ID and email are required"

    # First, try to find by google_id
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        # Update email and name if changed
        if user.email != email.lower():
            user.email = email.lower()
        if user.name != name:
            user.name = name
        if profile_picture and user.profile_picture != profile_picture:
            user.profile_picture = profile_picture
        db.session.commit()
        return user, None

    # Check if email is already used by a different auth method
    existing_user = User.query.filter_by(email=email.lower()).first()
    if existing_user:
        if existing_user.auth_provider == "google":
            # Same user, update google_id
            existing_user.google_id = google_id
            if profile_picture:
                existing_user.profile_picture = profile_picture
            db.session.commit()
            return existing_user, None
        else:
            # Email already used by email/password user
            return None, "Email address already registered with different login method"

    # Create new user
    user = User(
        email=email.lower().strip(),
        name=name.strip() if name else email.split("@")[0],
        profile_picture=profile_picture,
        google_id=google_id,
        auth_provider="google",
        password_hash=None,  # No password for Google users
    )

    db.session.add(user)
    db.session.commit()

    return user, None


def get_user_by_id(user_id):
    """Get user by ID.

    Args:
        user_id: User's UUID

    Returns:
        User or None
    """
    return User.query.filter_by(id=user_id, is_active=True).first()


def generate_oauth_state():
    """Generate a secure random state parameter for OAuth.

    Returns:
        str: Secure random state string
    """
    return secrets.token_urlsafe(32)

"""Configuration for TradeLogger."""

import os
from datetime import timedelta
from pathlib import Path


class Config:
    """Base configuration."""

    BASE_DIR = Path(__file__).parent.parent
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://localhost/tradelogger"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCREENSHOT_DIR = BASE_DIR / "screenshots"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY", "jwt-secret-key-change-in-production-min-32-chars"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/callback"
    )

    # Cookie Security
    JWT_COOKIE_SECURE = False  # Set to True in production (HTTPS only)
    JWT_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://tradelogger:tradelogger@localhost:5432/tradelogger_dev",
    )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    def __init__(self):
        """Validate required configuration."""
        super().__init__()
        if not os.environ.get("SECRET_KEY"):
            raise ValueError(
                "SECRET_KEY environment variable must be set in production"
            )
        if not os.environ.get("JWT_SECRET_KEY"):
            raise ValueError(
                "JWT_SECRET_KEY environment variable must be set in production"
            )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

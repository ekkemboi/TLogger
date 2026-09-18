"""Flask application factory for TradeLogger."""

import os
from pathlib import Path

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from src.config import config
from src.models import Account, User, db

# Initialize CSRF protection
csrf = CSRFProtect()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(
        __name__, template_folder="../web/templates", static_folder="../web/static"
    )
    app.config.from_object(config[config_name])

    # Session secret for OAuth state
    app.secret_key = app.config["SECRET_KEY"]

    Path(app.config["SCREENSHOT_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Configure CORS with credentials support
    # Allow all origins for API requests (needed for Electron file:// protocol)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "supports_credentials": True,
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            }
        },
    )

    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )

        # Strict Transport Security (only in production)
        if not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
    }

    swagger_template = {
        "info": {
            "title": "TradeLogger API",
            "description": "Trade logging system API with trade capture from TradingView",
            "version": "1.0.0",
        },
        "basePath": "/api",
        "schemes": ["http", "https"],
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    from src.routes.auth import auth_bp, oauth
    from src.routes.oauth import oauth_bp
    from src.routes.trades import trades_bp
    from src.routes.metrics import metrics_bp
    from src.routes.favorites import favorites_bp
    from src.routes.accounts import accounts_bp
    from src.routes.backtest import backtest_bp
    from src.routes.import_routes import import_bp
    from src.routes.analytics_routes import analytics_bp
    from src.routes.broker_routes import brokers_bp
    from web.routes import web_bp

    # Initialize OAuth
    oauth.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(oauth_bp, url_prefix="/api")
    app.register_blueprint(trades_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(favorites_bp, url_prefix="/api")
    app.register_blueprint(accounts_bp, url_prefix="/api")
    app.register_blueprint(backtest_bp, url_prefix="/api/backtest")
    app.register_blueprint(import_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(brokers_bp, url_prefix="/api")
    app.register_blueprint(web_bp)

    # Exempt API routes from CSRF (they use JWT tokens)
    csrf.exempt(auth_bp)
    csrf.exempt(oauth_bp)
    csrf.exempt(trades_bp)
    csrf.exempt(metrics_bp)
    csrf.exempt(favorites_bp)
    csrf.exempt(accounts_bp)
    csrf.exempt(backtest_bp)
    csrf.exempt(import_bp)
    csrf.exempt(analytics_bp)
    csrf.exempt(brokers_bp)

    with app.app_context():
        # Note: Database schema is managed by Alembic migrations
        # Run `alembic upgrade head` to create/update schema
        # db.create_all() is no longer used in production/development

        # For testing mode, create tables and seed data
        if app.config.get("TESTING"):
            db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

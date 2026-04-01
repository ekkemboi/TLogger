"""Flask application factory for TradeLogger."""

import os
from pathlib import Path

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS

from src.config import config
from src.models import Account, User, db


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

    # Configure CORS with credentials support
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5000", "http://localhost:3000"],
                "supports_credentials": True,
            }
        },
    )

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
    from src.routes.trades import trades_bp
    from src.routes.metrics import metrics_bp
    from src.routes.favorites import favorites_bp
    from src.routes.accounts import accounts_bp
    from web.routes import web_bp

    # Initialize OAuth
    oauth.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(trades_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(favorites_bp, url_prefix="/api")
    app.register_blueprint(accounts_bp, url_prefix="/api")
    app.register_blueprint(web_bp)

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

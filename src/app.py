"""Flask application factory for TradeLogger."""

import os
from pathlib import Path

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS

from src.config import config
from src.models import Account, db


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(
        __name__, template_folder="../web/templates", static_folder="../web/static"
    )
    app.config.from_object(config[config_name])

    Path(app.config["SCREENSHOT_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

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

    from src.routes.trades import trades_bp
    from src.routes.metrics import metrics_bp
    from src.routes.favorites import favorites_bp
    from src.routes.accounts import accounts_bp
    from web.routes import web_bp

    app.register_blueprint(trades_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(favorites_bp, url_prefix="/api")
    app.register_blueprint(accounts_bp, url_prefix="/api")
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()

        # Auto-create Default account if none exists (skip in testing mode)
        if not app.config.get("TESTING") and not Account.query.first():
            default_account = Account(name="Default")
            db.session.add(default_account)
            db.session.commit()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

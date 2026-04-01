"""Web routes for serving templates."""

from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def dashboard():
    """Render dashboard."""
    return render_template("dashboard.html")


@web_bp.route("/trades")
def trades():
    """Render trades list."""
    return render_template("trades.html")


@web_bp.route("/favorites")
def favorites():
    """Render favorites page."""
    return render_template("favorites.html")


@web_bp.route("/accounts")
def accounts():
    """Render accounts page."""
    return render_template("accounts.html")

"""Web routes for serving templates."""

from functools import wraps

import jwt
from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from src.models import Account

web_bp = Blueprint("web", __name__)


def login_required(f):
    """Decorator to require authentication for web routes.

    Checks for valid JWT access token in cookies.
    If not authenticated, redirects to login page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("access_token")

        if not token:
            return redirect(url_for("web.login", redirect=request.path))

        try:
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            # Store user info in Flask g object for use in templates
            g.current_user_id = payload["sub"]
            g.current_user_email = payload["email"]
        except jwt.ExpiredSignatureError:
            # Token expired, redirect to login
            return redirect(url_for("web.login", redirect=request.path))
        except jwt.InvalidTokenError:
            # Invalid token, redirect to login
            return redirect(url_for("web.login", redirect=request.path))

        return f(*args, **kwargs)

    return decorated_function


@web_bp.route("/")
@login_required
def dashboard():
    """Render dashboard."""
    return render_template("dashboard.html")


@web_bp.route("/trades")
@login_required
def trades():
    """Render trades list."""
    return render_template("trades.html")


@web_bp.route("/favorites")
@login_required
def favorites():
    """Render favorites page."""
    return render_template("favorites.html")


@web_bp.route("/accounts")
@login_required
def accounts():
    """Render accounts page."""
    return render_template("accounts.html")


@web_bp.route("/login")
def login():
    """Render login page.

    If user is already authenticated, redirect to dashboard.
    """
    # Check if already authenticated
    token = request.cookies.get("access_token")
    if token:
        try:
            jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            # Already authenticated, redirect to dashboard or requested page
            redirect_url = request.args.get("redirect", "/")
            return redirect(redirect_url)
        except jwt.ExpiredSignatureError:
            pass  # Token expired, show login page
        except jwt.InvalidTokenError:
            pass  # Invalid token, show login page

    return render_template("login.html")


@web_bp.route("/partials/account-dropdown")
@login_required
def account_dropdown_partial():
    """Return account dropdown partial for HTMX OOB updates."""
    accounts = Account.query.all()
    return render_template("partials/account_dropdown.html", accounts=accounts)


def get_accounts_for_template():
    """Helper to get accounts for OOB updates."""
    try:
        return Account.query.all()
    except Exception:
        return []

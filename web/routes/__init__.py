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


def is_htmx_request():
    """Check if current request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


def render_content_only(template_name, **context):
    """Render only the content block from a template for HTMX requests.

    This reads the template file, extracts the content block, and renders it directly
    without extending base.html.
    """
    from flask import current_app
    import os
    import re

    # Get template path
    template_path = os.path.join(
        current_app.root_path, "web", "templates", template_name
    )

    # Read template content
    with open(template_path, "r") as f:
        template_content = f.read()

    # Extract content block
    pattern = r"{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}"
    match = re.search(pattern, template_content, re.DOTALL)

    if match:
        content_template = match.group(1).strip()

        # Also extract scripts block if present
        scripts_pattern = r"{%\s*block\s+scripts\s*%}(.*?){%\s*endblock\s*%}"
        scripts_match = re.search(scripts_pattern, template_content, re.DOTALL)
        if scripts_match:
            scripts_template = scripts_match.group(1).strip()
            content_template += "\n" + scripts_template

        # Render just the content block
        from flask import render_template_string

        return render_template_string(content_template, **context)

    # Fallback: render full template
    return render_template(template_name, **context)


@web_bp.route("/")
@login_required
def dashboard():
    """Render dashboard."""
    if is_htmx_request():
        # Return only content for HTMX requests (no base template wrapper)
        return render_template("dashboard.html", htmx_request=True)
    return render_template("dashboard.html")


@web_bp.route("/trades")
@login_required
def trades():
    """Render trades list."""
    if is_htmx_request():
        return render_template("trades.html", htmx_request=True)
    return render_template("trades.html")


@web_bp.route("/favorites")
@login_required
def favorites():
    """Render favorites page."""
    if is_htmx_request():
        return render_template("favorites.html", htmx_request=True)
    return render_template("favorites.html")


@web_bp.route("/accounts")
@login_required
def accounts():
    """Render accounts page."""
    if is_htmx_request():
        accounts_list = get_accounts_for_template()
        return render_template(
            "accounts.html", htmx_request=True, accounts=accounts_list
        )
    return render_template("accounts.html")


@web_bp.route("/backtest")
@login_required
def backtest():
    """Render backtest page."""
    if is_htmx_request():
        return render_template("backtest.html", htmx_request=True)
    return render_template("backtest.html")


@web_bp.route("/import")
@login_required
def import_page():
    """Render CSV import page."""
    if is_htmx_request():
        return render_template("import.html", htmx_request=True)
    return render_template("import.html")


@web_bp.route("/analytics")
@login_required
def analytics():
    """Render analytics page."""
    if is_htmx_request():
        return render_template("analytics.html", htmx_request=True)
    return render_template("analytics.html")


@web_bp.route("/brokers")
@login_required
def brokers():
    """Render broker connections page."""
    if is_htmx_request():
        return render_template("brokers.html", htmx_request=True)
    return render_template("brokers.html")


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

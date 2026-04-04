"""Authentication routes for TradeLogger."""

import jwt
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, jsonify, request, session, url_for

from src.models import User
from src.services import auth_service
from src.utils.jwt_utils import (
    clear_auth_cookies,
    generate_access_token,
    generate_refresh_token,
    jwt_required,
    set_auth_cookies,
    verify_refresh_token,
)

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()


def get_google_client():
    """Get or create Google OAuth client.

    Returns:
        OAuth client or None if not configured
    """
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    if "google" not in oauth._clients:
        oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    return oauth.google


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user with email and password.

    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: Password123!
            name:
              type: string
              example: John Doe
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
      400:
        description: Validation error
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "")
    name = data.get("name", "").strip()

    user, error = auth_service.register_user(email, password, name)
    if error:
        return jsonify({"error": error}), 400

    # Generate tokens
    access_token = generate_access_token(user.id, user.email)
    refresh_token = generate_refresh_token(user.id)

    response = jsonify(
        {"message": "User registered successfully", "user": user.to_dict()}
    )
    response.status_code = 201
    set_auth_cookies(response, access_token, refresh_token)

    return response


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Login with email and password.

    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: Password123!
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "")

    user, error = auth_service.authenticate_user(email, password)
    if error:
        return jsonify({"error": error}), 401

    # Generate tokens
    access_token = generate_access_token(user.id, user.email)
    refresh_token = generate_refresh_token(user.id)

    response = jsonify({"message": "Login successful", "user": user.to_dict()})
    set_auth_cookies(response, access_token, refresh_token)

    return response


@auth_bp.route("/auth/google/login")
def google_login():
    """Initiate Google OAuth login flow.

    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirect to Google OAuth
      503:
        description: Google OAuth not configured
    """
    google = get_google_client()
    if not google:
        return jsonify({"error": "Google OAuth not configured"}), 503

    # Generate and store state for CSRF protection
    state = auth_service.generate_oauth_state()
    session["oauth_state"] = state

    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI")
    return google.authorize_redirect(redirect_uri, state=state)


@auth_bp.route("/auth/callback")
def google_callback():
    """Handle Google OAuth callback.

    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirect to dashboard on success, login on failure
    """
    google = get_google_client()
    if not google:
        return jsonify({"error": "Google OAuth not configured"}), 503

    # Verify state parameter for CSRF protection
    state = request.args.get("state")
    stored_state = session.pop("oauth_state", None)

    if not state or state != stored_state:
        return jsonify({"error": "Invalid state parameter"}), 400

    try:
        # Get token and user info from Google
        token = google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            return jsonify({"error": "Failed to get user info from Google"}), 400

        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0])
        picture = user_info.get("picture")

        # Get or create user
        user, error = auth_service.get_or_create_google_user(
            google_id, email, name, picture
        )
        if error:
            return jsonify({"error": error}), 400

        # Generate tokens
        access_token = generate_access_token(user.id, user.email)
        refresh_token = generate_refresh_token(user.id)

        response = jsonify({"message": "Login successful", "user": user.to_dict()})
        set_auth_cookies(response, access_token, refresh_token)

        return response

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 400


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token.

    Supports both cookie-based and Authorization header-based refresh token.

    ---
    tags:
      - Authentication
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            message:
              type: string
            access_token:
              type: string
            refresh_token:
              type: string
      401:
        description: Invalid refresh token
    """
    refresh_token_value = None

    # Try Authorization header first (for desktop widget)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        refresh_token_value = auth_header[7:]

    # Fall back to cookie
    if not refresh_token_value:
        refresh_token_value = request.cookies.get("refresh_token")

    if not refresh_token_value:
        return jsonify({"error": "Refresh token required"}), 401

    payload = verify_refresh_token(refresh_token_value)
    if not payload:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    user_id = payload["sub"]
    user = auth_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    # Generate new tokens
    access_token = generate_access_token(user.id, user.email)
    new_refresh_token = generate_refresh_token(user.id)

    # Return tokens in JSON for desktop widget, or set cookies for web
    response_data = {
        "message": "Token refreshed successfully",
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }

    response = jsonify(response_data)

    # Also set cookies for web clients
    set_auth_cookies(response, access_token, new_refresh_token)

    return response


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Logout and clear authentication cookies.

    ---
    tags:
      - Authentication
    responses:
      200:
        description: Logout successful
    """
    response = jsonify({"message": "Logout successful"})
    clear_auth_cookies(response)
    return response


@auth_bp.route("/auth/me")
@jwt_required
def get_current_user():
    """Get current authenticated user information.

    ---
    tags:
      - Authentication
    responses:
      200:
        description: Current user info
        schema:
          type: object
      401:
        description: Not authenticated
    """
    from flask import g

    user = auth_service.get_user_by_id(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


@auth_bp.route("/auth/status")
def auth_status():
    """Check if user is authenticated (public endpoint).

    Supports both cookie-based and Authorization header-based authentication.

    ---
    tags:
      - Authentication
    responses:
      200:
        description: Authentication status
        schema:
          type: object
          properties:
            authenticated:
              type: boolean
            user:
              type: object
    """
    from flask import g
    from src.utils.jwt_utils import verify_access_token

    token = None

    # Try to get token from Authorization header first (for desktop widget)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Fall back to cookie
    if not token:
        token = request.cookies.get("access_token")

    if token:
        payload = verify_access_token(token)
        if payload:
            user = auth_service.get_user_by_id(payload["sub"])
            if user:
                return jsonify({"authenticated": True, "user": user.to_dict()})

    return jsonify({"authenticated": False, "user": None})


@auth_bp.route("/auth/desktop-callback")
def desktop_auth_callback():
    """Redirect endpoint for desktop app authentication.

    After browser login, redirects to custom protocol URL with tokens.

    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirect to tradelogger:// protocol URL with tokens
    """
    from flask import redirect

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token:
        try:
            from src.utils.jwt_utils import decode_token

            decode_token(access_token)

            # Get remember_me preference from query param or default to false
            remember_me = request.args.get("remember_me", "false").lower() == "true"

            # Include tokens in protocol URL for desktop widget
            return redirect(
                f"tradelogger://auth?status=success"
                f"&access_token={access_token}"
                f"&refresh_token={refresh_token}"
                f"&remember_me={str(remember_me).lower()}"
            )
        except jwt.ExpiredSignatureError:
            return redirect("tradelogger://auth?status=expired")
        except jwt.InvalidTokenError:
            return redirect("tradelogger://auth?status=invalid")

    return redirect("tradelogger://auth?status=unauthenticated")

"""OAuth 2.0 routes for secure authentication flow.

This module provides OAuth 2.0 Authorization Code flow endpoints
with PKCE support for secure desktop authentication.

Endpoints:
    POST /api/oauth/authorize - Initiate OAuth flow
    GET  /api/oauth/callback  - Handle callback (returns code)
    POST /api/oauth/token     - Exchange code for tokens
"""

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from src.services import auth_service, oauth_service
from src.utils.jwt_utils import generate_access_token, generate_refresh_token

oauth_bp = Blueprint("oauth", __name__)


@oauth_bp.route("/oauth/authorize", methods=["GET"])
def authorize():
    """Initiate OAuth 2.0 authorization flow.

    This endpoint is called by the desktop app to start the OAuth flow.
    It stores OAuth parameters in session and redirects to the login page.

    Query Parameters:
        redirect_uri: The primary callback URI (e.g., "tradelogger://auth")
        fallback_uri: The fallback callback URI (e.g., "http://127.0.0.1:PORT/callback")
        code_challenge: The PKCE code challenge (BASE64URL_SHA256_HASH)
        state: Optional state parameter for CSRF protection
        response_type: Must be "code"

    Returns:
        Redirects to the login page with oauth_flow=true

    Note:
        The actual authentication happens in the browser.
        After login, the browser redirects to the callback with the code.
    """
    current_app.logger.info(
        f"OAuth authorize request: redirect_uri={request.args.get('redirect_uri')}, fallback_uri={request.args.get('fallback_uri')}"
    )

    # Validate required fields from query parameters
    redirect_uri = request.args.get("redirect_uri")
    code_challenge = request.args.get("code_challenge")
    response_type = request.args.get("response_type")

    if not redirect_uri:
        return jsonify({"error": "redirect_uri is required"}), 400

    if not code_challenge:
        return jsonify({"error": "code_challenge is required for PKCE"}), 400

    if response_type != "code":
        return jsonify({"error": "response_type must be 'code'"}), 400

    # Store OAuth parameters in session for callback validation
    session["oauth_redirect_uri"] = redirect_uri
    session["oauth_fallback_uri"] = request.args.get("fallback_uri")
    session["oauth_code_challenge"] = code_challenge
    session["oauth_state"] = request.args.get("state")
    session["oauth_source"] = "desktop"

    # Redirect to login page with OAuth flag
    current_app.logger.info("Redirecting to login page with oauth_flow=true")
    return redirect(url_for("web.login", oauth_flow="true"))


@oauth_bp.route("/oauth/callback", methods=["GET"])
def callback():
    """Handle OAuth callback after user authentication.

    This endpoint is called after the user logs in successfully.
    It generates an authorization code and redirects to the callback URI.

    Query Parameters:
        code: The authorization code
        state: Optional state parameter (CSRF protection)

    Returns:
        Redirects to redirect_uri or fallback_uri with:
            ?code=AUTH_CODE&state=STATE

    Note:
        This endpoint requires the user to be authenticated.
        The actual login happens via the /auth/login or /auth/google/login endpoints.
    """
    from flask import g
    from src.utils.jwt_utils import verify_access_token

    # Get token from query param or cookie
    token = request.args.get("token")
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return jsonify({"error": "Authentication required"}), 401

    # Verify token
    payload = verify_access_token(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Check OAuth session first (before user lookup)
    code_challenge = session.get("oauth_code_challenge")
    if not code_challenge:
        return jsonify({"error": "OAuth session expired"}), 400

    # Get user
    user = auth_service.get_user_by_id(payload["sub"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get OAuth parameters from session
    redirect_uri = session.pop("oauth_redirect_uri", None)
    fallback_uri = session.pop("oauth_fallback_uri", None)
    expected_state = session.pop("oauth_state", None)
    received_state = request.args.get("state")

    current_app.logger.info(
        f"OAuth callback: redirect_uri={redirect_uri}, fallback_uri={fallback_uri}"
    )

    # Validate state parameter (CSRF protection)
    if expected_state and expected_state != received_state:
        return jsonify({"error": "Invalid state parameter"}), 400

    # Use primary redirect URI or fallback
    callback_uri = redirect_uri or fallback_uri
    if not callback_uri:
        current_app.logger.error("OAuth callback: No callback URI configured")
        return jsonify({"error": "No callback URI configured"}), 400

    current_app.logger.info(f"OAuth callback: Using callback_uri={callback_uri}")

    # Create authorization code
    auth_code = oauth_service.create_auth_code(
        user_id=user.id,
        code_challenge=code_challenge,
        redirect_uri=callback_uri,
        state=received_state,
    )

    # Build callback URL with code
    callback_url = f"{callback_uri}?code={auth_code}"
    if received_state:
        callback_url += f"&state={received_state}"

    current_app.logger.info(f"OAuth callback: Redirecting to {callback_url}")

    # Clear auth cookies (they were temporary for the OAuth flow)
    from src.utils.jwt_utils import clear_auth_cookies

    response = jsonify({"redirect_url": callback_url})
    clear_auth_cookies(response)

    return response


@oauth_bp.route("/oauth/token", methods=["POST"])
def token():
    """Exchange authorization code for access and refresh tokens.

    This endpoint exchanges the short-lived authorization code
    for long-lived access and refresh tokens.

    Request Body:
        {
            "code": "AUTHORIZATION_CODE",
            "code_verifier": "PKCE_CODE_VERIFIER",
            "grant_type": "authorization_code"
        }

    Returns:
        {
            "access_token": "JWT_ACCESS_TOKEN",
            "refresh_token": "JWT_REFRESH_TOKEN",
            "token_type": "Bearer",
            "expires_in": 3600
        }

    Error Responses:
        400: Invalid request
        401: Invalid code or verifier
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Validate grant type
    grant_type = data.get("grant_type")
    if grant_type != "authorization_code":
        return jsonify({"error": "Unsupported grant_type"}), 400

    code = data.get("code")
    code_verifier = data.get("code_verifier")

    if not code or not code_verifier:
        return jsonify({"error": "code and code_verifier are required"}), 400

    # Exchange code for user
    auth_code = oauth_service.exchange_code(
        code=code,
        code_verifier=code_verifier,
        expected_redirect_uri=data.get("redirect_uri", "tradelogger://auth"),
    )

    if not auth_code:
        return jsonify({"error": "Invalid or expired authorization code"}), 401

    # Get user
    user = auth_service.get_user_by_id(auth_code.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    # Generate tokens
    access_token = generate_access_token(user.id, user.email)
    refresh_token = generate_refresh_token(user.id)

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,  # 1 hour
        }
    )


@oauth_bp.route("/oauth/pkce", methods=["GET"])
def generate_pkce():
    """Generate PKCE code verifier and challenge.

    This is a helper endpoint for clients that need to generate
    PKCE parameters before initiating the OAuth flow.

    Returns:
        {
            "code_verifier": "RANDOM_STRING",
            "code_challenge": "BASE64URL_SHA256_HASH",
            "method": "S256"
        }

    Note:
        The code_verifier should be kept secret by the client.
        Only the code_challenge should be sent to the server.
    """
    code_verifier, code_challenge = oauth_service.generate_pkce()

    return jsonify(
        {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "method": "S256",
        }
    )

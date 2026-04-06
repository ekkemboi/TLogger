"""OAuth 2.0 service with PKCE support for secure authentication.

This module implements the OAuth 2.0 Authorization Code flow with PKCE
(Proof Key for Code Exchange) for secure desktop authentication.

PKCE prevents authorization code interception attacks by binding the
authorization code to the specific client request.
"""

import base64
import hashlib
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from src.models import User
from src.services import auth_service


@dataclass
class OAuthCode:
    """Represents an OAuth authorization code.

    Attributes:
        code: The authorization code string
        user_id: ID of the authenticated user
        code_challenge: PKCE code challenge (S256 hash of verifier)
        redirect_uri: The redirect URI used in the request
        created_at: Unix timestamp when code was created
        used: Whether the code has been exchanged for tokens
        state: Optional state parameter for CSRF protection
    """

    code: str
    user_id: str
    code_challenge: str
    redirect_uri: str
    created_at: float = field(default_factory=time.time)
    used: bool = False
    state: Optional[str] = None


class OAuthService:
    """Service for managing OAuth 2.0 flows with PKCE.

    This service handles:
    - Authorization code generation and storage (in-memory)
    - PKCE code challenge/verifier validation
    - Token exchange
    - Automatic code expiration (10 minutes)

    Codes are stored in-memory and lost on server restart.
    This is acceptable because codes are single-use and short-lived.
    """

    CODE_EXPIRY_SECONDS = 600  # 10 minutes

    def __init__(self):
        """Initialize the OAuth service with thread-safe storage."""
        self._codes: dict[str, OAuthCode] = {}
        self._lock = threading.Lock()

    def generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)

        The code_verifier is a cryptographically random string.
        The code_challenge is the base64url-encoded SHA256 hash of the verifier.
        """
        # Generate 32 bytes of random data (256 bits)
        code_verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("ascii")
            .rstrip("=")
        )

        # Create code_challenge = BASE64URL(SHA256(code_verifier))
        code_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            )
            .decode("ascii")
            .rstrip("=")
        )

        return code_verifier, code_challenge

    def verify_pkce(self, code_verifier: str, code_challenge: str) -> bool:
        """Verify that a code verifier matches a code challenge.

        Args:
            code_verifier: The PKCE code verifier from the client
            code_challenge: The stored PKCE code challenge

        Returns:
            True if the verifier generates the challenge, False otherwise
        """
        # Recompute the challenge from the verifier
        computed_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            )
            .decode("ascii")
            .rstrip("=")
        )

        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(computed_challenge, code_challenge)

    def generate_code(self) -> str:
        """Generate a cryptographically secure authorization code.

        Returns:
            A URL-safe base64-encoded random string
        """
        return (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("ascii")
            .rstrip("=")
        )

    def generate_state(self) -> str:
        """Generate a state parameter for CSRF protection.

        Returns:
            A cryptographically secure random string
        """
        return secrets.token_urlsafe(32)

    def create_auth_code(
        self,
        user_id: str,
        code_challenge: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """Create and store a new authorization code.

        Args:
            user_id: ID of the authenticated user
            code_challenge: PKCE code challenge from the client
            redirect_uri: The redirect URI that will receive the code
            state: Optional state parameter for CSRF protection

        Returns:
            The generated authorization code
        """
        code = self.generate_code()

        auth_code = OAuthCode(
            code=code,
            user_id=user_id,
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
            state=state,
        )

        with self._lock:
            # Clean up expired codes before adding new one
            self._cleanup_expired_codes()
            self._codes[code] = auth_code

        return code

    def exchange_code(
        self, code: str, code_verifier: str, expected_redirect_uri: str
    ) -> Optional[OAuthCode]:
        """Exchange an authorization code for tokens.

        This validates:
        1. Code exists and hasn't been used
        2. Code hasn't expired (10 minutes)
        3. PKCE verifier matches the challenge
        4. Redirect URI matches what was registered

        Args:
            code: The authorization code
            code_verifier: The PKCE code verifier
            expected_redirect_uri: The redirect URI to validate against

        Returns:
            The OAuthCode if valid, None otherwise

        Note:
            The code is marked as used and cannot be exchanged again.
        """
        with self._lock:
            # Clean up expired codes
            self._cleanup_expired_codes()

            # Check if code exists
            if code not in self._codes:
                return None

            auth_code = self._codes[code]

            # Check if code was already used
            if auth_code.used:
                return None

            # Check if code has expired
            if time.time() - auth_code.created_at > self.CODE_EXPIRY_SECONDS:
                del self._codes[code]
                return None

            # Verify PKCE
            if not self.verify_pkce(code_verifier, auth_code.code_challenge):
                return None

            # Verify redirect URI matches
            if auth_code.redirect_uri != expected_redirect_uri:
                return None

            # Mark code as used (single-use only)
            auth_code.used = True

            return auth_code

    def get_code(self, code: str) -> Optional[OAuthCode]:
        """Get an authorization code without consuming it.

        This is useful for validation before exchange.

        Args:
            code: The authorization code

        Returns:
            The OAuthCode if found and valid, None otherwise
        """
        with self._lock:
            self._cleanup_expired_codes()
            return self._codes.get(code)

    def _cleanup_expired_codes(self) -> None:
        """Remove expired authorization codes from storage.

        This is called automatically when codes are accessed.
        """
        current_time = time.time()
        expired_codes = [
            code
            for code, auth_code in self._codes.items()
            if current_time - auth_code.created_at > self.CODE_EXPIRY_SECONDS
        ]
        for code in expired_codes:
            del self._codes[code]

    def cleanup_all_codes(self) -> int:
        """Manually clean up all expired codes.

        Returns:
            Number of codes removed
        """
        with self._lock:
            initial_count = len(self._codes)
            self._cleanup_expired_codes()
            return initial_count - len(self._codes)


# Global OAuth service instance
oauth_service = OAuthService()

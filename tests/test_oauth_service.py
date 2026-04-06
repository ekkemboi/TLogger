"""Tests for OAuth 2.0 service with PKCE support."""

import pytest
import time
from src.services.oauth_service import OAuthService, OAuthCode, oauth_service


class TestPKCEGeneration:
    """Test PKCE code verifier and challenge generation."""

    def test_generate_pkce_returns_tuple(self):
        """Test that generate_pkce returns a tuple of two strings."""
        service = OAuthService()
        verifier, challenge = service.generate_pkce()

        assert isinstance(verifier, str)
        assert isinstance(challenge, str)
        assert len(verifier) > 0
        assert len(challenge) > 0

    def test_pkce_verifier_format(self):
        """Test that code verifier is base64url encoded."""
        service = OAuthService()
        verifier, _ = service.generate_pkce()

        # Base64url should not contain +, /, or =
        assert "+" not in verifier
        assert "/" not in verifier
        assert "=" not in verifier

    def test_pkce_challenge_is_sha256_hash(self):
        """Test that code challenge is SHA256 hash of verifier."""
        import base64
        import hashlib

        service = OAuthService()
        verifier, challenge = service.generate_pkce()

        # Manually compute challenge
        expected_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
            .decode("ascii")
            .rstrip("=")
        )

        assert challenge == expected_challenge

    def test_pkce_verifier_unique(self):
        """Test that each generated verifier is unique."""
        service = OAuthService()
        verifiers = set()

        for _ in range(10):
            verifier, _ = service.generate_pkce()
            assert verifier not in verifiers
            verifiers.add(verifier)


class TestPKCEVerification:
    """Test PKCE code challenge verification."""

    def test_verify_pkce_success(self):
        """Test successful PKCE verification."""
        service = OAuthService()
        verifier, challenge = service.generate_pkce()

        assert service.verify_pkce(verifier, challenge) is True

    def test_verify_pkce_failure_wrong_verifier(self):
        """Test PKCE verification fails with wrong verifier."""
        service = OAuthService()
        _, challenge = service.generate_pkce()
        wrong_verifier = "wrong_verifier_string"

        assert service.verify_pkce(wrong_verifier, challenge) is False

    def test_verify_pkce_failure_tampered_challenge(self):
        """Test PKCE verification fails with tampered challenge."""
        service = OAuthService()
        verifier, _ = service.generate_pkce()
        tampered_challenge = "tampered_challenge"

        assert service.verify_pkce(verifier, tampered_challenge) is False


class TestAuthCodeCreation:
    """Test authorization code creation and storage."""

    def test_create_auth_code_returns_string(self):
        """Test that create_auth_code returns a code string."""
        service = OAuthService()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge="challenge-abc",
            redirect_uri="tradelogger://auth",
        )

        assert isinstance(code, str)
        assert len(code) > 0

    def test_create_auth_code_stores_data(self):
        """Test that created code stores correct data."""
        service = OAuthService()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge="challenge-abc",
            redirect_uri="tradelogger://auth",
            state="state-xyz",
        )

        auth_code = service.get_code(code)
        assert auth_code is not None
        assert auth_code.user_id == "user-123"
        assert auth_code.code_challenge == "challenge-abc"
        assert auth_code.redirect_uri == "tradelogger://auth"
        assert auth_code.state == "state-xyz"
        assert auth_code.used is False

    def test_create_auth_code_cleans_expired(self):
        """Test that creating a code cleans up expired codes."""
        service = OAuthService()

        # Create an expired code by manipulating time
        old_code = service.create_auth_code(
            user_id="old-user",
            code_challenge="old-challenge",
            redirect_uri="tradelogger://auth",
        )

        # Make the code appear expired
        service._codes[old_code].created_at = time.time() - 700  # 11 minutes ago

        # Create a new code - should clean up the expired one
        new_code = service.create_auth_code(
            user_id="new-user",
            code_challenge="new-challenge",
            redirect_uri="tradelogger://auth",
        )

        # Old code should be gone
        assert service.get_code(old_code) is None
        # New code should exist
        assert service.get_code(new_code) is not None


class TestAuthCodeExchange:
    """Test authorization code exchange."""

    def test_exchange_code_success(self):
        """Test successful code exchange."""
        service = OAuthService()

        # Generate PKCE pair
        verifier, challenge = service.generate_pkce()

        # Create code
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge=challenge,
            redirect_uri="tradelogger://auth",
        )

        # Exchange code
        auth_code = service.exchange_code(
            code=code,
            code_verifier=verifier,
            expected_redirect_uri="tradelogger://auth",
        )

        assert auth_code is not None
        assert auth_code.user_id == "user-123"
        assert auth_code.used is True

    def test_exchange_code_invalid_code(self):
        """Test exchange fails with invalid code."""
        service = OAuthService()

        result = service.exchange_code(
            code="invalid-code",
            code_verifier="verifier",
            expected_redirect_uri="tradelogger://auth",
        )

        assert result is None

    def test_exchange_code_wrong_verifier(self):
        """Test exchange fails with wrong PKCE verifier."""
        service = OAuthService()

        _, challenge = service.generate_pkce()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge=challenge,
            redirect_uri="tradelogger://auth",
        )

        result = service.exchange_code(
            code=code,
            code_verifier="wrong-verifier",
            expected_redirect_uri="tradelogger://auth",
        )

        assert result is None

    def test_exchange_code_wrong_redirect_uri(self):
        """Test exchange fails with wrong redirect URI."""
        service = OAuthService()

        verifier, challenge = service.generate_pkce()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge=challenge,
            redirect_uri="tradelogger://auth",
        )

        result = service.exchange_code(
            code=code, code_verifier=verifier, expected_redirect_uri="wrong://uri"
        )

        assert result is None

    def test_exchange_code_already_used(self):
        """Test exchange fails if code was already used."""
        service = OAuthService()

        verifier, challenge = service.generate_pkce()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge=challenge,
            redirect_uri="tradelogger://auth",
        )

        # First exchange should succeed
        first_result = service.exchange_code(
            code=code,
            code_verifier=verifier,
            expected_redirect_uri="tradelogger://auth",
        )
        assert first_result is not None

        # Second exchange should fail
        second_result = service.exchange_code(
            code=code,
            code_verifier=verifier,
            expected_redirect_uri="tradelogger://auth",
        )
        assert second_result is None

    def test_exchange_code_expired(self):
        """Test exchange fails with expired code."""
        service = OAuthService()

        verifier, challenge = service.generate_pkce()
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge=challenge,
            redirect_uri="tradelogger://auth",
        )

        # Make code expired
        service._codes[code].created_at = time.time() - 700  # 11 minutes ago

        result = service.exchange_code(
            code=code,
            code_verifier=verifier,
            expected_redirect_uri="tradelogger://auth",
        )

        assert result is None


class TestCodeExpiration:
    """Test code expiration functionality."""

    def test_code_expires_after_10_minutes(self):
        """Test that codes expire after 10 minutes."""
        service = OAuthService()

        # Default expiry is 600 seconds (10 minutes)
        assert service.CODE_EXPIRY_SECONDS == 600

    def test_cleanup_expired_codes(self):
        """Test manual cleanup of expired codes."""
        service = OAuthService()

        # Create a code
        code = service.create_auth_code(
            user_id="user-123",
            code_challenge="challenge",
            redirect_uri="tradelogger://auth",
        )

        # Make it expired
        service._codes[code].created_at = time.time() - 700

        # Cleanup should remove it
        removed_count = service.cleanup_all_codes()
        assert removed_count == 1
        assert service.get_code(code) is None

    def test_get_code_cleans_expired(self):
        """Test that get_code cleans up expired codes."""
        service = OAuthService()

        code = service.create_auth_code(
            user_id="user-123",
            code_challenge="challenge",
            redirect_uri="tradelogger://auth",
        )

        # Make it expired
        service._codes[code].created_at = time.time() - 700

        # get_code should return None and clean it up
        result = service.get_code(code)
        assert result is None


class TestGlobalService:
    """Test the global OAuth service instance."""

    def test_global_service_exists(self):
        """Test that global oauth_service exists."""
        assert oauth_service is not None
        assert isinstance(oauth_service, OAuthService)

    def test_global_service_thread_safe(self):
        """Test that global service is thread-safe."""
        import threading

        codes = []

        def create_code():
            code = oauth_service.create_auth_code(
                user_id="thread-test",
                code_challenge="challenge",
                redirect_uri="tradelogger://auth",
            )
            codes.append(code)

        # Create codes from multiple threads
        threads = [threading.Thread(target=create_code) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All codes should be unique
        assert len(codes) == len(set(codes))

"""
Ephemeral token service for WebSocket authentication.

Manages short-lived tokens for browser clients to connect
without exposing API keys.
"""

import hashlib
import logging
from datetime import timedelta
from typing import Optional
from uuid import UUID

from django.core.cache import cache
from django.utils import timezone

from apps.api_keys.models import APIKey
from apps.realtime.models import EphemeralToken

logger = logging.getLogger(__name__)


class TokenClaims:
    """Claims extracted from a validated token."""

    def __init__(
        self,
        tenant_id: UUID,
        api_key_id: UUID,
        session_config: dict,
        expires_at: int,
    ):
        """
        Initializes TokenClaims with extracted data.

        Args:
            tenant_id: The UUID of the tenant.
            api_key_id: The UUID of the API key used.
            session_config: The session configuration associated with the token.
            expires_at: Unix timestamp when the token expires.
        """
        self.tenant_id = tenant_id
        self.api_key_id = api_key_id
        self.session_config = session_config
        self.expires_at = expires_at


class EphemeralTokenService:
    """
    Manages ephemeral tokens for WebSocket authentication.

    Tokens are stored in both Redis (for fast lookup) and PostgreSQL
    (for audit trail). Redis entries have TTL for automatic expiration.
    """

    TOKEN_PREFIX = "realtime:token:"
    DEFAULT_TTL = 60  # seconds

    def __init__(self):
        """Initializes the EphemeralTokenService."""
        self.cache = cache

    async def create_token(
        self,
        tenant_id: UUID,
        api_key: APIKey,
        session_config: Optional[dict] = None,
        ttl: int = DEFAULT_TTL,
    ) -> tuple[str, int]:
        """
        Create a new ephemeral token.

        Args:
            tenant_id: Tenant UUID
            api_key: API key that created this token
            session_config: Pre-configured session settings
            ttl: Token TTL in seconds

        Returns:
            Tuple of (token_value, expires_at_timestamp)
        """
        # Generate token
        full_token, prefix, token_hash = EphemeralToken.generate_token()

        # Calculate expiration
        expires_at = timezone.now() + timedelta(seconds=ttl)
        expires_timestamp = int(expires_at.timestamp())

        # Store in database for audit
        token_record = await EphemeralToken.objects.acreate(
            token_hash=token_hash,
            token_prefix=prefix,
            tenant_id=tenant_id,
            api_key=api_key,
            session_config=session_config or {},
            expires_at=expires_at,
        )

        # Store in Redis for fast lookup
        cache_key = f"{self.TOKEN_PREFIX}{token_hash}"
        cache_data = {
            "tenant_id": str(tenant_id),
            "api_key_id": str(api_key.id),
            "session_config": session_config or {},
            "expires_at": expires_timestamp,
            "token_id": str(token_record.pk) if hasattr(token_record, "pk") else None,
        }

        # Use sync cache API (Django's cache is sync by default)
        self.cache.set(cache_key, cache_data, timeout=ttl)

        logger.info(
            f"Created ephemeral token {prefix}... for tenant {tenant_id}, "
            f"expires in {ttl}s"
        )

        return full_token, expires_timestamp

    async def validate_token(self, token: str) -> Optional[TokenClaims]:
        """
        Validate an ephemeral token.

        Args:
            token: The full token value

        Returns:
            TokenClaims if valid, None if invalid/expired
        """
        # Hash the token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        cache_key = f"{self.TOKEN_PREFIX}{token_hash}"

        # Try Redis first (fast path)
        cache_data = self.cache.get(cache_key)

        if cache_data:
            # Check expiration
            if cache_data["expires_at"] < int(timezone.now().timestamp()):
                logger.warning(f"Token expired: {token[:12]}...")
                return None

            return TokenClaims(
                tenant_id=UUID(cache_data["tenant_id"]),
                api_key_id=UUID(cache_data["api_key_id"]),
                session_config=cache_data["session_config"],
                expires_at=cache_data["expires_at"],
            )

        # Fallback to database (slow path)
        try:
            token_record = (
                await EphemeralToken.objects.filter(
                    token_hash=token_hash,
                    used=False,
                )
                .select_related("api_key")
                .afirst()
            )

            if not token_record:
                logger.warning(f"Token not found: {token[:12]}...")
                return None

            if not token_record.is_valid:
                logger.warning(f"Token invalid/expired: {token[:12]}...")
                return None

            return TokenClaims(
                tenant_id=token_record.tenant_id,
                api_key_id=token_record.api_key_id,
                session_config=token_record.session_config,
                expires_at=int(token_record.expires_at.timestamp()),
            )

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def mark_token_used(
        self,
        token: str,
        session_id: str,
    ) -> bool:
        """
        Mark a token as used after successful WebSocket connection.

        Args:
            token: The full token value
            session_id: ID of the created session

        Returns:
            True if marked successfully
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            # Update database record
            updated = await EphemeralToken.objects.filter(
                token_hash=token_hash,
                used=False,
            ).aupdate(
                used=True,
                used_at=timezone.now(),
                session_id=session_id,
            )

            if updated:
                # Remove from Redis cache
                cache_key = f"{self.TOKEN_PREFIX}{token_hash}"
                self.cache.delete(cache_key)

                logger.info(
                    f"Token {token[:12]}... marked as used for session {session_id}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error marking token as used: {e}")
            return False

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke an ephemeral token.

        Args:
            token: The full token value

        Returns:
            True if revoked successfully
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            # Delete from Redis
            cache_key = f"{self.TOKEN_PREFIX}{token_hash}"
            self.cache.delete(cache_key)

            # Mark as used in database (prevents reuse)
            await EphemeralToken.objects.filter(
                token_hash=token_hash,
            ).aupdate(
                used=True,
                used_at=timezone.now(),
            )

            logger.info(f"Token {token[:12]}... revoked")
            return True

        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from database.

        Returns:
            Number of tokens deleted
        """
        try:
            deleted, _ = await EphemeralToken.objects.filter(
                expires_at__lt=timezone.now(),
            ).adelete()

            if deleted:
                logger.info(f"Cleaned up {deleted} expired tokens")

            return deleted

        except Exception as e:
            logger.error(f"Error cleaning up tokens: {e}")
            return 0


# Singleton instance
ephemeral_token_service = EphemeralTokenService()

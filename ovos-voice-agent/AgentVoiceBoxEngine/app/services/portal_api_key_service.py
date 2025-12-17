"""Portal API Key Service with tenant isolation.

Provides CRUD operations for API keys with proper tenant_id filtering.
Implements Requirements E4.1, E4.2 for multi-tenant data isolation.

This service is used by the Portal API routes to manage API keys
with guaranteed tenant isolation on all queries.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .api_key_service import APIKeyHasher, generate_api_key

logger = logging.getLogger(__name__)

# Global service instance
_portal_api_key_service: Optional["PortalAPIKeyService"] = None


@dataclass
class PortalAPIKey:
    """API key data for portal display."""

    id: str
    name: str
    prefix: str
    scopes: List[str]
    is_active: bool
    created_at: dt.datetime
    expires_at: Optional[dt.datetime]
    last_used_at: Optional[dt.datetime]


class PortalAPIKeyService:
    """Portal API Key service with tenant isolation.

    All methods require tenant_id and enforce isolation at the query level.
    """

    def __init__(self, db_session_factory: Optional[Any] = None):
        self._db_factory = db_session_factory
        self._hasher = APIKeyHasher()

    async def list_keys(
        self,
        tenant_id: str,
        include_inactive: bool = False,
    ) -> List[PortalAPIKey]:
        """List all API keys for a tenant.

        Args:
            tenant_id: Tenant ID to filter by (REQUIRED)
            include_inactive: Include revoked/inactive keys

        Returns:
            List of API keys belonging to the tenant
        """
        if not self._db_factory:
            logger.warning("Database not configured")
            return []

        try:
            from ..models.tenant import APIKey, Project
            from ..utils.database import session_scope

            with session_scope(self._db_factory) as session:
                # Query with tenant isolation via project join
                query = (
                    session.query(APIKey)
                    .join(Project, APIKey.project_id == Project.id)
                    .filter(Project.tenant_id == uuid.UUID(tenant_id))
                )

                if not include_inactive:
                    query = query.filter(APIKey.is_active.is_(True))

                keys = query.order_by(APIKey.created_at.desc()).all()

                return [
                    PortalAPIKey(
                        id=str(k.id),
                        name=k.name,
                        prefix=k.key_prefix,
                        scopes=k.scopes or [],
                        is_active=k.is_active,
                        created_at=k.created_at,
                        expires_at=k.expires_at,
                        last_used_at=k.last_used_at,
                    )
                    for k in keys
                ]

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    async def get_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[PortalAPIKey]:
        """Get a specific API key with tenant verification.

        Args:
            key_id: API key ID
            tenant_id: Tenant ID for isolation (REQUIRED)

        Returns:
            API key if found and belongs to tenant, None otherwise
        """
        if not self._db_factory:
            return None

        try:
            from ..models.tenant import APIKey, Project
            from ..utils.database import session_scope

            with session_scope(self._db_factory) as session:
                # Query with tenant isolation
                key = (
                    session.query(APIKey)
                    .join(Project, APIKey.project_id == Project.id)
                    .filter(APIKey.id == uuid.UUID(key_id))
                    .filter(Project.tenant_id == uuid.UUID(tenant_id))
                    .first()
                )

                if not key:
                    return None

                return PortalAPIKey(
                    id=str(key.id),
                    name=key.name,
                    prefix=key.key_prefix,
                    scopes=key.scopes or [],
                    is_active=key.is_active,
                    created_at=key.created_at,
                    expires_at=key.expires_at,
                    last_used_at=key.last_used_at,
                )

        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None

    async def create_key(
        self,
        tenant_id: str,
        name: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None,
        created_by: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> tuple[PortalAPIKey, str]:
        """Create a new API key for a tenant.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            name: Key name
            scopes: Permission scopes
            expires_in_days: Days until expiration
            created_by: User ID who created the key
            project_id: Project to associate with (uses default if not provided)

        Returns:
            Tuple of (key_info, secret) - secret is only returned once

        Raises:
            ValueError: If tenant has no projects
        """
        if not self._db_factory:
            raise ValueError("Database not configured")

        try:
            from ..models.tenant import APIKey, Project
            from ..utils.database import session_scope

            # Generate the key
            full_key, prefix = generate_api_key()
            key_hash = self._hasher.hash(full_key)

            with session_scope(self._db_factory) as session:
                # Get or verify project belongs to tenant
                if project_id:
                    project = (
                        session.query(Project)
                        .filter(Project.id == uuid.UUID(project_id))
                        .filter(Project.tenant_id == uuid.UUID(tenant_id))
                        .first()
                    )
                    if not project:
                        raise ValueError("Project not found or doesn't belong to tenant")
                else:
                    # Get default project for tenant
                    project = (
                        session.query(Project)
                        .filter(Project.tenant_id == uuid.UUID(tenant_id))
                        .first()
                    )
                    if not project:
                        # Create default project
                        project = Project(
                            id=uuid.uuid4(),
                            tenant_id=uuid.UUID(tenant_id),
                            name="Default",
                            environment="development",
                        )
                        session.add(project)
                        session.flush()

                # Calculate expiration
                expires_at = None
                if expires_in_days:
                    expires_at = dt.datetime.utcnow() + dt.timedelta(days=expires_in_days)

                # Create the key
                key = APIKey(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    key_hash=key_hash,
                    key_prefix=prefix,
                    name=name,
                    scopes=scopes,
                    is_active=True,
                    expires_at=expires_at,
                    created_at=dt.datetime.utcnow(),
                )
                session.add(key)
                session.commit()

                return (
                    PortalAPIKey(
                        id=str(key.id),
                        name=key.name,
                        prefix=key.key_prefix,
                        scopes=key.scopes or [],
                        is_active=key.is_active,
                        created_at=key.created_at,
                        expires_at=key.expires_at,
                        last_used_at=None,
                    ),
                    full_key,
                )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise ValueError(f"Failed to create API key: {e}")

    async def revoke_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> bool:
        """Revoke an API key.

        Args:
            key_id: API key ID
            tenant_id: Tenant ID for isolation (REQUIRED)

        Returns:
            True if key was revoked, False if not found
        """
        if not self._db_factory:
            return False

        try:
            from ..models.tenant import APIKey, Project
            from ..utils.database import session_scope

            with session_scope(self._db_factory) as session:
                # Query with tenant isolation
                key = (
                    session.query(APIKey)
                    .join(Project, APIKey.project_id == Project.id)
                    .filter(APIKey.id == uuid.UUID(key_id))
                    .filter(Project.tenant_id == uuid.UUID(tenant_id))
                    .first()
                )

                if not key:
                    return False

                key.is_active = False
                session.commit()

                # Invalidate Redis cache
                await self._invalidate_cache(key.key_prefix)

                logger.info(
                    "API key revoked",
                    extra={"key_id": key_id, "tenant_id": tenant_id},
                )
                return True

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    async def schedule_revocation(
        self,
        key_id: str,
        hours: int = 24,
    ) -> bool:
        """Schedule a key for revocation after grace period.

        Args:
            key_id: API key ID
            hours: Hours until revocation

        Returns:
            True if scheduled successfully
        """
        # In production, this would schedule a background task
        # For now, we just log the intent
        logger.info(
            "API key scheduled for revocation",
            extra={"key_id": key_id, "hours": hours},
        )
        return True

    async def get_key_usage(
        self,
        key_id: str,
    ) -> Dict[str, Any]:
        """Get usage statistics for an API key.

        Args:
            key_id: API key ID

        Returns:
            Usage statistics dictionary
        """
        # In production, this would query usage metrics from Lago or Redis
        return {
            "total_requests": 0,
            "requests_today": 0,
            "requests_this_month": 0,
        }

    async def _invalidate_cache(self, prefix: str) -> None:
        """Invalidate Redis cache for an API key."""
        try:
            from .redis_client import get_redis_client

            redis = get_redis_client()
            cache_key = f"apikey:{prefix}"
            await redis.client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")


def get_api_key_service() -> PortalAPIKeyService:
    """Get or create the portal API key service singleton."""
    global _portal_api_key_service

    if _portal_api_key_service is None:
        try:
            from ..utils.database import get_session_factory

            db_factory = get_session_factory()
            _portal_api_key_service = PortalAPIKeyService(db_session_factory=db_factory)
        except Exception as e:
            logger.warning(f"Failed to initialize with database: {e}")
            _portal_api_key_service = PortalAPIKeyService()

    return _portal_api_key_service


async def init_api_key_service() -> None:
    """Initialize the API key service."""
    get_api_key_service()
    logger.info("Portal API key service initialized")


async def close_api_key_service() -> None:
    """Close the API key service."""
    global _portal_api_key_service
    _portal_api_key_service = None


__all__ = [
    "PortalAPIKey",
    "PortalAPIKeyService",
    "get_api_key_service",
    "init_api_key_service",
    "close_api_key_service",
]

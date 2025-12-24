"""
WebSocket middleware for authentication and tenant context.
"""
import logging
from typing import Optional
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class WebSocketAuthMiddleware:
    """
    WebSocket authentication middleware.

    Validates JWT tokens and sets user/tenant context on the scope.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process WebSocket connection."""
        # Extract token from query string or headers
        token = self._get_token(scope)

        if token:
            # Validate token and set user
            user, tenant_id = await self._authenticate(token)
            scope["user"] = user
            scope["tenant_id"] = tenant_id
        else:
            scope["user"] = AnonymousUser()
            scope["tenant_id"] = None

        return await self.app(scope, receive, send)

    def _get_token(self, scope) -> Optional[str]:
        """Extract token from connection."""
        # Try query string first
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        if "token" in query_params:
            return query_params["token"][0]

        # Try headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return None

    @database_sync_to_async
    def _authenticate(self, token: str):
        """Authenticate token and return user and tenant_id."""
        from apps.users.models import User
        from integrations.keycloak import keycloak_client

        try:
            # Validate JWT token
            claims = keycloak_client.validate_token(token)

            # Get user from database
            user = User.objects.filter(keycloak_id=claims.sub).first()

            if user:
                return user, claims.tenant_id

            return AnonymousUser(), claims.tenant_id

        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            return AnonymousUser(), None

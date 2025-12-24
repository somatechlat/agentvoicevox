"""
Base WebSocket consumer with authentication and tenant context.
"""
import logging
from typing import Any, Dict, Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from apps.tenants.models import Tenant
from apps.users.models import User
from integrations.keycloak import keycloak_client

logger = logging.getLogger(__name__)


class BaseConsumer(AsyncJsonWebsocketConsumer):
    """
    Base WebSocket consumer with authentication.

    Provides:
    - JWT token validation
    - Tenant context
    - Ping/pong heartbeat
    - Error handling
    """

    # Close codes
    CLOSE_NORMAL = 1000
    CLOSE_AUTH_FAILED = 4001
    CLOSE_TENANT_INVALID = 4002
    CLOSE_TENANT_SUSPENDED = 4003
    CLOSE_RATE_LIMITED = 4029

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[User] = None
        self.tenant: Optional[Tenant] = None
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.authenticated = False

    async def connect(self):
        """Handle WebSocket connection."""
        # Authenticate before accepting
        if not await self._authenticate():
            await self.close(code=self.CLOSE_AUTH_FAILED)
            return

        # Validate tenant
        if not await self._validate_tenant():
            return

        # Accept connection
        await self.accept()
        self.authenticated = True

        # Join tenant group for broadcasts
        if self.tenant_id:
            await self.channel_layer.group_add(
                f"tenant_{self.tenant_id}",
                self.channel_name,
            )

        # Join user group for direct messages
        if self.user_id:
            await self.channel_layer.group_add(
                f"user_{self.user_id}",
                self.channel_name,
            )

        logger.info(
            f"WebSocket connected: user={self.user_id}, tenant={self.tenant_id}"
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave groups
        if self.tenant_id:
            await self.channel_layer.group_discard(
                f"tenant_{self.tenant_id}",
                self.channel_name,
            )

        if self.user_id:
            await self.channel_layer.group_discard(
                f"user_{self.user_id}",
                self.channel_name,
            )

        logger.info(
            f"WebSocket disconnected: user={self.user_id}, code={close_code}"
        )

    async def receive_json(self, content: Dict[str, Any], **kwargs):
        """Handle incoming JSON message."""
        message_type = content.get("type", "")

        # Handle ping/pong heartbeat
        if message_type == "ping":
            await self.send_json({"type": "pong"})
            return

        # Dispatch to handler
        handler = getattr(self, f"handle_{message_type}", None)
        if handler:
            try:
                await handler(content)
            except Exception as e:
                logger.error(f"Error handling {message_type}: {e}")
                await self.send_error("internal_error", str(e))
        else:
            await self.send_error("unknown_message_type", f"Unknown type: {message_type}")

    async def _authenticate(self) -> bool:
        """Authenticate the WebSocket connection."""
        # Get token from query string or headers
        token = self._get_token()
        if not token:
            logger.warning("WebSocket connection without token")
            return False

        try:
            # Validate JWT token
            claims = keycloak_client.validate_token(token)

            self.user_id = claims.sub
            self.tenant_id = claims.tenant_id

            # Load user from database
            from apps.users.models import User

            self.user = await User.objects.filter(keycloak_id=claims.sub).afirst()

            return True

        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            return False

    def _get_token(self) -> Optional[str]:
        """Extract token from connection."""
        # Try query string first
        query_string = self.scope.get("query_string", b"").decode()
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param[6:]

        # Try headers
        headers = dict(self.scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return None

    async def _validate_tenant(self) -> bool:
        """Validate tenant context."""
        if not self.tenant_id:
            await self.close(code=self.CLOSE_TENANT_INVALID)
            return False

        try:
            self.tenant = await Tenant.objects.filter(id=self.tenant_id).afirst()

            if not self.tenant:
                await self.close(code=self.CLOSE_TENANT_INVALID)
                return False

            if self.tenant.status == Tenant.Status.SUSPENDED:
                await self.close(code=self.CLOSE_TENANT_SUSPENDED)
                return False

            return True

        except Exception as e:
            logger.error(f"Tenant validation failed: {e}")
            await self.close(code=self.CLOSE_TENANT_INVALID)
            return False

    async def send_error(self, code: str, message: str, details: Dict = None):
        """Send error message to client."""
        await self.send_json({
            "type": "error",
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        })

    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send event to client."""
        await self.send_json({
            "type": event_type,
            "data": data,
        })

    # Group message handlers
    async def tenant_message(self, event: Dict[str, Any]):
        """Handle message sent to tenant group."""
        await self.send_json(event["message"])

    async def user_message(self, event: Dict[str, Any]):
        """Handle message sent to user group."""
        await self.send_json(event["message"])

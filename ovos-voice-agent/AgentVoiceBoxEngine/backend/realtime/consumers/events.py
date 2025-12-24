"""
Event streaming WebSocket consumer.

Streams tenant-wide and user-specific notifications.
"""
import logging
from typing import Any, Dict

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class EventConsumer(BaseConsumer):
    """
    Event streaming consumer.

    Streams:
    - Tenant-wide notifications
    - User-specific notifications
    - System events
    """

    async def connect(self):
        """Handle connection and subscribe to event streams."""
        await super().connect()

        if self.authenticated:
            # Subscribe to additional event groups
            await self.channel_layer.group_add(
                f"events_{self.tenant_id}",
                self.channel_name,
            )

            # Send connection confirmation
            await self.send_event("connected", {
                "tenant_id": str(self.tenant_id),
                "user_id": st
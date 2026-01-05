"""
Event streaming WebSocket consumer.

Streams tenant-wide and user-specific notifications.
"""

import logging
from typing import Any

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
            await self.send_event(
                "connected",
                {
                    "tenant_id": str(self.tenant_id),
                    "user_id": str(self.user_id) if self.user_id else None,
                },
            )

    async def disconnect(self, close_code):
        """Handle disconnection."""
        if self.tenant_id:
            await self.channel_layer.group_discard(
                f"events_{self.tenant_id}",
                self.channel_name,
            )

        await super().disconnect(close_code)

    async def handle_subscribe(self, content: dict[str, Any]):
        """Handle subscription to specific event types."""
        event_types = content.get("event_types", [])

        for event_type in event_types:
            group_name = f"events_{self.tenant_id}_{event_type}"
            await self.channel_layer.group_add(group_name, self.channel_name)

        await self.send_event("subscribed", {"event_types": event_types})

    async def handle_unsubscribe(self, content: dict[str, Any]):
        """Handle unsubscription from event types."""
        event_types = content.get("event_types", [])

        for event_type in event_types:
            group_name = f"events_{self.tenant_id}_{event_type}"
            await self.channel_layer.group_discard(group_name, self.channel_name)

        await self.send_event("unsubscribed", {"event_types": event_types})

    # Event handlers for group messages
    async def notification_event(self, event: dict[str, Any]):
        """Handle notification event from group."""
        await self.send_event("notification", event["data"])

    async def billing_event(self, event: dict[str, Any]):
        """Handle billing event from group."""
        await self.send_event("billing", event["data"])

    async def session_event(self, event: dict[str, Any]):
        """Handle session event from group."""
        await self.send_event("session", event["data"])

    async def system_event(self, event: dict[str, Any]):
        """Handle system event from group."""
        await self.send_event("system", event["data"])

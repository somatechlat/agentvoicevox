"""
Kafka integration client.

Provides event streaming via Apache Kafka.
Used for:
- Audit event publishing
- Cross-service communication
- Real-time analytics
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class KafkaEvent:
    """Kafka event structure."""

    topic: str
    key: Optional[str] = None
    value: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "key": self.key,
            "value": self.value,
            "headers": self.headers,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class KafkaClient:
    """
    Kafka client for event streaming.

    Handles:
    - Event publishing
    - Event consumption
    - Topic management
    """

    # Standard topics
    TOPIC_AUDIT = "agentvoicebox.audit"
    TOPIC_SESSIONS = "agentvoicebox.sessions"
    TOPIC_BILLING = "agentvoicebox.billing"
    TOPIC_NOTIFICATIONS = "agentvoicebox.notifications"
    TOPIC_METRICS = "agentvoicebox.metrics"

    def __init__(self):
        """Initialize Kafka client from Django settings."""
        kafka_config = getattr(settings, "KAFKA", {})
        self.bootstrap_servers = kafka_config.get("BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer_group = kafka_config.get("CONSUMER_GROUP", "agentvoicebox-backend")
        self.enabled = kafka_config.get("ENABLED", False)
        self.security_protocol = kafka_config.get("SECURITY_PROTOCOL", "PLAINTEXT")

        self._producer = None
        self._consumer = None

    def _get_producer(self):
        """Get or create Kafka producer."""
        if not self.enabled:
            return None

        if self._producer is None:
            try:
                from confluent_kafka import Producer

                config = {
                    "bootstrap.servers": self.bootstrap_servers,
                    "security.protocol": self.security_protocol,
                    "client.id": f"{self.consumer_group}-producer",
                    "acks": "all",
                    "retries": 3,
                    "retry.backoff.ms": 100,
                }

                self._producer = Producer(config)
                logger.info(f"Kafka producer connected to {self.bootstrap_servers}")

            except ImportError:
                logger.warning("confluent-kafka not installed, Kafka disabled")
                self.enabled = False
                return None
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                return None

        return self._producer

    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation."""
        if err:
            logger.error(f"Kafka delivery failed: {err}")
        else:
            logger.debug(f"Kafka message delivered to {msg.topic()}[{msg.partition()}]")

    async def publish(self, event: KafkaEvent) -> bool:
        """
        Publish an event to Kafka.

        Args:
            event: KafkaEvent to publish

        Returns:
            True if published successfully
        """
        if not self.enabled:
            logger.debug(f"Kafka disabled, skipping event: {event.topic}")
            return True

        producer = self._get_producer()
        if not producer:
            return False

        try:
            # Serialize value to JSON
            value_bytes = json.dumps(event.value).encode("utf-8")

            # Serialize key if present
            key_bytes = event.key.encode("utf-8") if event.key else None

            # Convert headers
            headers = [(k, v.encode("utf-8")) for k, v in event.headers.items()]

            # Add standard headers
            headers.append(("event_id", event.event_id.encode("utf-8")))
            if event.timestamp:
                headers.append(("timestamp", event.timestamp.isoformat().encode("utf-8")))

            producer.produce(
                topic=event.topic,
                key=key_bytes,
                value=value_bytes,
                headers=headers,
                callback=self._delivery_callback,
            )

            # Trigger delivery
            producer.poll(0)

            return True

        except Exception as e:
            logger.error(f"Failed to publish Kafka event: {e}")
            return False

    async def publish_audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: str,
        tenant_id: str,
        details: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Publish an audit event.

        Args:
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID
            actor_id: Actor who performed the action
            tenant_id: Tenant context
            details: Additional details

        Returns:
            True if published
        """
        event = KafkaEvent(
            topic=self.TOPIC_AUDIT,
            key=tenant_id,
            value={
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "actor_id": actor_id,
                "tenant_id": tenant_id,
                "details": details or {},
            },
            timestamp=datetime.utcnow(),
        )
        return await self.publish(event)

    async def publish_session_event(
        self,
        event_type: str,
        session_id: str,
        tenant_id: str,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Publish a session event.

        Args:
            event_type: Type of session event
            session_id: Session ID
            tenant_id: Tenant context
            data: Event data

        Returns:
            True if published
        """
        event = KafkaEvent(
            topic=self.TOPIC_SESSIONS,
            key=session_id,
            value={
                "event_type": event_type,
                "session_id": session_id,
                "tenant_id": tenant_id,
                "data": data or {},
            },
            timestamp=datetime.utcnow(),
        )
        return await self.publish(event)

    async def publish_billing_event(
        self,
        event_type: str,
        tenant_id: str,
        usage: dict[str, Any],
    ) -> bool:
        """
        Publish a billing event.

        Args:
            event_type: Type of billing event
            tenant_id: Tenant ID
            usage: Usage data

        Returns:
            True if published
        """
        event = KafkaEvent(
            topic=self.TOPIC_BILLING,
            key=tenant_id,
            value={
                "event_type": event_type,
                "tenant_id": tenant_id,
                "usage": usage,
            },
            timestamp=datetime.utcnow(),
        )
        return await self.publish(event)

    async def publish_notification(
        self,
        notification_type: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Publish a notification event.

        Args:
            notification_type: Type of notification
            tenant_id: Tenant ID
            user_id: Target user (optional, None for tenant-wide)
            data: Notification data

        Returns:
            True if published
        """
        event = KafkaEvent(
            topic=self.TOPIC_NOTIFICATIONS,
            key=user_id or tenant_id,
            value={
                "notification_type": notification_type,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "data": data or {},
            },
            timestamp=datetime.utcnow(),
        )
        return await self.publish(event)

    def flush(self, timeout: float = 10.0) -> int:
        """
        Flush pending messages.

        Args:
            timeout: Timeout in seconds

        Returns:
            Number of messages still in queue
        """
        if not self.enabled or not self._producer:
            return 0

        return self._producer.flush(timeout)

    def close(self) -> None:
        """Close Kafka connections."""
        if self._producer:
            self._producer.flush(10.0)
            self._producer = None
            logger.info("Kafka producer closed")

        if self._consumer:
            self._consumer.close()
            self._consumer = None
            logger.info("Kafka consumer closed")


# Singleton instance
kafka_client = KafkaClient()

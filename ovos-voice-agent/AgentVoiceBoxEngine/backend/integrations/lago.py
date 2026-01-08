"""
Lago billing integration client.

Provides usage-based billing via Lago.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional, Union

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class PlanCode(str, Enum):
    """Available billing plan codes."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    PRO_ANNUAL = "pro_annual"
    ENTERPRISE = "enterprise"


class MetricCode(str, Enum):
    """Billable metric codes."""

    API_REQUESTS = "api_requests"
    AUDIO_MINUTES_INPUT = "audio_minutes_input"
    AUDIO_MINUTES_OUTPUT = "audio_minutes_output"
    LLM_TOKENS_INPUT = "llm_tokens_input"
    LLM_TOKENS_OUTPUT = "llm_tokens_output"
    CONCURRENT_CONNECTIONS = "concurrent_connections"
    CONNECTION_MINUTES = "connection_minutes"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    ACTIVE = "active"
    PENDING = "pending"
    TERMINATED = "terminated"
    CANCELED = "canceled"


class InvoiceStatus(str, Enum):
    """Invoice status values."""

    DRAFT = "draft"
    FINALIZED = "finalized"
    VOIDED = "voided"


@dataclass
class LagoCustomer:
    """Lago customer representation."""

    lago_id: str
    external_id: str
    name: str
    email: str
    currency: str = "USD"
    timezone: str = "UTC"
    billing_configuration: dict[str, Any] = field(default_factory=dict)
    metadata: list[dict[str, str]] = field(default_factory=list)
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LagoCustomer":
        """Create customer from Lago API response."""
        customer = data.get("customer", data)
        created_at = None
        if customer.get("created_at"):
            created_at = datetime.fromisoformat(
                customer["created_at"].replace("Z", "+00:00")
            )
        return cls(
            lago_id=customer.get("lago_id", ""),
            external_id=customer.get("external_id", ""),
            name=customer.get("name", ""),
            email=customer.get("email", ""),
            currency=customer.get("currency", "USD"),
            timezone=customer.get("timezone", "UTC"),
            billing_configuration=customer.get("billing_configuration", {}),
            metadata=customer.get("metadata", []),
            created_at=created_at,
        )


@dataclass
class LagoSubscription:
    """Lago subscription representation."""

    lago_id: str
    external_id: str
    external_customer_id: str
    plan_code: str
    status: SubscriptionStatus
    name: Optional[str] = None
    started_at: Optional[datetime] = None
    ending_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LagoSubscription":
        """Create subscription from Lago API response."""
        sub = data.get("subscription", data)

        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            """
            Parses an ISO 8601 string from Lago API into a timezone-aware datetime object.

            Args:
                val: The ISO 8601 string (e.g., "2023-01-01T12:00:00Z").

            Returns:
                A timezone-aware datetime object, or None if the input is None.
            """
            if not val:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            lago_id=sub.get("lago_id", ""),
            external_id=sub.get("external_id", ""),
            external_customer_id=sub.get("external_customer_id", ""),
            plan_code=sub.get("plan_code", ""),
            status=SubscriptionStatus(sub.get("status", "pending")),
            name=sub.get("name"),
            started_at=parse_dt(sub.get("started_at")),
            ending_at=parse_dt(sub.get("ending_at")),
            terminated_at=parse_dt(sub.get("terminated_at")),
            canceled_at=parse_dt(sub.get("canceled_at")),
            created_at=parse_dt(sub.get("created_at")),
        )


@dataclass
class LagoInvoice:
    """Lago invoice representation."""

    lago_id: str
    sequential_id: int
    number: str
    status: InvoiceStatus
    payment_status: str
    currency: str
    total_amount_cents: int
    taxes_amount_cents: int
    sub_total_excluding_taxes_amount_cents: int
    issuing_date: Optional[datetime] = None
    payment_due_date: Optional[datetime] = None
    file_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LagoInvoice":
        """Create invoice from Lago API response."""
        inv = data.get("invoice", data)

        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            """
            Parses an ISO 8601 string from Lago API into a timezone-aware datetime object.

            Args:
                val: The ISO 8601 string (e.g., "2023-01-01T12:00:00Z").

            Returns:
                A timezone-aware datetime object, or None if the input is None.
            """
            if not val:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            lago_id=inv.get("lago_id", ""),
            sequential_id=inv.get("sequential_id", 0),
            number=inv.get("number", ""),
            status=InvoiceStatus(inv.get("status", "draft")),
            payment_status=inv.get("payment_status", "pending"),
            currency=inv.get("currency", "USD"),
            total_amount_cents=inv.get("total_amount_cents", 0),
            taxes_amount_cents=inv.get("taxes_amount_cents", 0),
            sub_total_excluding_taxes_amount_cents=inv.get(
                "sub_total_excluding_taxes_amount_cents", 0
            ),
            issuing_date=parse_dt(inv.get("issuing_date")),
            payment_due_date=parse_dt(inv.get("payment_due_date")),
            file_url=inv.get("file_url"),
        )


@dataclass
class UsageEvent:
    """Usage event for metering."""

    transaction_id: str
    external_customer_id: str
    code: str
    timestamp: datetime
    properties: dict[str, Any] = field(default_factory=dict)
    external_subscription_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Lago API format."""
        data = {
            "transaction_id": self.transaction_id,
            "external_customer_id": self.external_customer_id,
            "code": self.code,
            "timestamp": int(self.timestamp.timestamp()),
            "properties": self.properties,
        }
        if self.external_subscription_id:
            data["external_subscription_id"] = self.external_subscription_id
        return data


class LagoClient:
    """
    Lago client for billing operations.

    Provides methods for:
    - Customer CRUD operations
    - Subscription management
    - Usage event metering (async pipeline)
    - Invoice retrieval
    """

    def __init__(self):
        """Initialize Lago client from Django settings."""
        self.api_url = settings.LAGO["API_URL"]
        self.api_key = settings.LAGO["API_KEY"]
        self.webhook_secret = settings.LAGO["WEBHOOK_SECRET"]
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0

        self._client: Optional[httpx.AsyncClient] = None
        self._event_queue: asyncio.Queue[UsageEvent] = asyncio.Queue(maxsize=10000)
        self._metering_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                base_url=self.api_url,
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make authenticated API request with retry logic."""
        client = await self._get_client()
        headers = kwargs.pop("headers", {})
        headers.update(self._headers())

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, path, headers=headers, **kwargs)
                return response
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    logger.warning(
                        f"Lago request failed (attempt {attempt + 1}), retrying: {e}"
                    )

        raise last_error or Exception("Request failed after retries")

    # =========================================================================
    # Customer Management
    # =========================================================================

    async def create_customer(
        self,
        external_id: str,
        name: str,
        email: str,
        currency: str = "USD",
        timezone: str = "UTC",
        metadata: Optional[list[dict[str, str]]] = None,
    ) -> LagoCustomer:
        """Create a new customer in Lago."""
        customer_data = {
            "customer": {
                "external_id": external_id,
                "name": name,
                "email": email,
                "currency": currency,
                "timezone": timezone,
            }
        }

        if metadata:
            customer_data["customer"]["metadata"] = metadata

        response = await self._request("POST", "/api/v1/customers", json=customer_data)
        response.raise_for_status()

        return LagoCustomer.from_dict(response.json())

    async def get_customer(self, external_id: str) -> Optional[LagoCustomer]:
        """Get customer by external ID."""
        response = await self._request("GET", f"/api/v1/customers/{external_id}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return LagoCustomer.from_dict(response.json())

    async def update_customer(
        self,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[list[dict[str, str]]] = None,
    ) -> LagoCustomer:
        """Update customer attributes."""
        update_data: dict[str, Any] = {"customer": {"external_id": external_id}}

        if name is not None:
            update_data["customer"]["name"] = name
        if email is not None:
            update_data["customer"]["email"] = email
        if metadata is not None:
            update_data["customer"]["metadata"] = metadata

        response = await self._request(
            "PUT", f"/api/v1/customers/{external_id}", json=update_data
        )
        response.raise_for_status()

        return LagoCustomer.from_dict(response.json())

    async def delete_customer(self, external_id: str) -> None:
        """Delete a customer."""
        response = await self._request("DELETE", f"/api/v1/customers/{external_id}")
        response.raise_for_status()

    # =========================================================================
    # Subscription Management
    # =========================================================================

    async def create_subscription(
        self,
        external_customer_id: str,
        plan_code: Union[str, PlanCode],
        external_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> LagoSubscription:
        """Create a new subscription."""
        if isinstance(plan_code, PlanCode):
            plan_code = plan_code.value

        if external_id is None:
            external_id = f"sub_{uuid.uuid4().hex[:16]}"

        sub_data = {
            "subscription": {
                "external_customer_id": external_customer_id,
                "plan_code": plan_code,
                "external_id": external_id,
                "billing_time": "calendar",
            }
        }

        if name:
            sub_data["subscription"]["name"] = name

        response = await self._request("POST", "/api/v1/subscriptions", json=sub_data)
        response.raise_for_status()

        return LagoSubscription.from_dict(response.json())

    async def get_subscription(self, external_id: str) -> Optional[LagoSubscription]:
        """Get subscription by external ID."""
        response = await self._request("GET", f"/api/v1/subscriptions/{external_id}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return LagoSubscription.from_dict(response.json())

    async def update_subscription(
        self,
        external_id: str,
        plan_code: Optional[Union[str, PlanCode]] = None,
    ) -> LagoSubscription:
        """Update subscription (upgrade/downgrade plan)."""
        update_data: dict[str, Any] = {"subscription": {}}

        if plan_code is not None:
            if isinstance(plan_code, PlanCode):
                plan_code = plan_code.value
            update_data["subscription"]["plan_code"] = plan_code

        response = await self._request(
            "PUT", f"/api/v1/subscriptions/{external_id}", json=update_data
        )
        response.raise_for_status()

        return LagoSubscription.from_dict(response.json())

    async def terminate_subscription(self, external_id: str) -> LagoSubscription:
        """Terminate a subscription immediately."""
        response = await self._request("DELETE", f"/api/v1/subscriptions/{external_id}")
        response.raise_for_status()

        return LagoSubscription.from_dict(response.json())

    # =========================================================================
    # Invoice Management
    # =========================================================================

    async def list_invoices(
        self,
        external_customer_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[LagoInvoice]:
        """List invoices with optional filtering."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}

        if external_customer_id:
            params["external_customer_id"] = external_customer_id
        if status:
            params["status"] = status.value

        response = await self._request("GET", "/api/v1/invoices", params=params)
        response.raise_for_status()

        data = response.json()
        return [LagoInvoice.from_dict(i) for i in data.get("invoices", [])]

    async def download_invoice(self, lago_id: str) -> Optional[str]:
        """Get invoice PDF download URL."""
        response = await self._request("POST", f"/api/v1/invoices/{lago_id}/download")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()
        return data.get("invoice", {}).get("file_url")

    # =========================================================================
    # Usage Metering
    # =========================================================================

    def queue_usage_event(
        self,
        external_customer_id: str,
        code: Union[str, MetricCode],
        properties: Optional[dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Queue a usage event for async sending."""
        if isinstance(code, MetricCode):
            code = code.value

        if transaction_id is None:
            transaction_id = f"evt_{uuid.uuid4().hex}"

        if timestamp is None:
            timestamp = datetime.now(UTC)

        event = UsageEvent(
            transaction_id=transaction_id,
            external_customer_id=external_customer_id,
            code=code,
            timestamp=timestamp,
            properties=properties or {},
        )

        try:
            self._event_queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            logger.warning("Usage event queue full, dropping event")
            return False

    async def send_usage_event(
        self,
        external_customer_id: str,
        code: Union[str, MetricCode],
        properties: Optional[dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Send a usage event immediately."""
        if isinstance(code, MetricCode):
            code = code.value

        if transaction_id is None:
            transaction_id = f"evt_{uuid.uuid4().hex}"

        if timestamp is None:
            timestamp = datetime.now(UTC)

        event_data = {
            "event": {
                "transaction_id": transaction_id,
                "external_customer_id": external_customer_id,
                "code": code,
                "timestamp": int(timestamp.timestamp()),
                "properties": properties or {},
            }
        }

        try:
            response = await self._request("POST", "/api/v1/events", json=event_data)
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Failed to send usage event: {e}")
            return False

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def track_api_request(self, tenant_id: str) -> bool:
        """Track an API request for billing."""
        return self.queue_usage_event(
            external_customer_id=tenant_id,
            code=MetricCode.API_REQUESTS,
        )

    def track_audio_input(self, tenant_id: str, duration_minutes: float) -> bool:
        """Track audio input (STT) for billing."""
        return self.queue_usage_event(
            external_customer_id=tenant_id,
            code=MetricCode.AUDIO_MINUTES_INPUT,
            properties={"duration_minutes": duration_minutes},
        )

    def track_audio_output(self, tenant_id: str, duration_minutes: float) -> bool:
        """Track audio output (TTS) for billing."""
        return self.queue_usage_event(
            external_customer_id=tenant_id,
            code=MetricCode.AUDIO_MINUTES_OUTPUT,
            properties={"duration_minutes": duration_minutes},
        )

    def track_llm_tokens(
        self, tenant_id: str, input_tokens: int, output_tokens: int
    ) -> bool:
        """Track LLM token usage for billing."""
        success = self.queue_usage_event(
            external_customer_id=tenant_id,
            code=MetricCode.LLM_TOKENS_INPUT,
            properties={"tokens": input_tokens},
        )
        success = success and self.queue_usage_event(
            external_customer_id=tenant_id,
            code=MetricCode.LLM_TOKENS_OUTPUT,
            properties={"tokens": output_tokens},
        )
        return success

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
lago_client = LagoClient()

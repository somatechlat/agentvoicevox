"""
PayPal payment integration client.

Provides subscription and payment processing via PayPal REST API.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class PayPalEnvironment(Enum):
    """PayPal API environment."""
    SANDBOX = "sandbox"
    LIVE = "live"


@dataclass
class PayPalOrder:
    """PayPal order result."""
    order_id: str
    status: str
    approval_url: Optional[str] = None


@dataclass
class PayPalSubscription:
    """PayPal subscription result."""
    subscription_id: str
    status: str
    plan_id: str


class PayPalClient:
    """
    PayPal client for payment processing.

    Supports:
    - Order creation and capture
    - Subscription management
    - Webhook handling
    """

    def __init__(self) -> None:
        """Initialize PayPal client from Django settings."""
        paypal_config = getattr(settings, "PAYPAL", {})

        required_keys = ["CLIENT_ID", "CLIENT_SECRET"]
        missing = [key for key in required_keys if key not in paypal_config]
        if missing:
            logger.warning(f"PayPal configuration missing keys: {', '.join(missing)}")

        self.client_id = paypal_config.get("CLIENT_ID", "")
        self.client_secret = paypal_config.get("CLIENT_SECRET", "")
        self.environment = PayPalEnvironment(
            paypal_config.get("ENVIRONMENT", "sandbox")
        )
        self.webhook_id = paypal_config.get("WEBHOOK_ID", "")
        self.enabled = paypal_config.get("ENABLED", False)
        self._access_token: Optional[str] = None

    @property
    def base_url(self) -> str:
        """Get PayPal API base URL based on environment."""
        if self.environment == PayPalEnvironment.LIVE:
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token from PayPal."""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def create_order(
        self,
        amount: str,
        currency: str = "USD",
        description: str = "",
        return_url: str = "",
        cancel_url: str = "",
    ) -> PayPalOrder:
        """
        Create a PayPal order for one-time payment.

        Args:
            amount: Order amount as string (e.g., "10.00")
            currency: ISO 4217 currency code
            description: Order description
            return_url: URL to redirect after approval
            cancel_url: URL to redirect on cancel

        Returns:
            PayPalOrder with order_id and approval_url
        """
        if not self.enabled:
            logger.warning("PayPal is disabled, returning mock order")
            return PayPalOrder(
                order_id="MOCK-ORDER-001",
                status="CREATED",
                approval_url="https://example.com/mock-approval",
            )

        token = await self._get_access_token()

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": amount,
                    },
                    "description": description,
                }
            ],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                json=order_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            approval_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break

            return PayPalOrder(
                order_id=data["id"],
                status=data["status"],
                approval_url=approval_url,
            )

    async def capture_order(self, order_id: str) -> PayPalOrder:
        """
        Capture an approved PayPal order.

        Args:
            order_id: The PayPal order ID to capture

        Returns:
            PayPalOrder with updated status
        """
        if not self.enabled:
            return PayPalOrder(order_id=order_id, status="COMPLETED")

        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            return PayPalOrder(
                order_id=data["id"],
                status=data["status"],
            )

    async def create_subscription(
        self,
        plan_id: str,
        subscriber_email: str,
        return_url: str = "",
        cancel_url: str = "",
    ) -> PayPalSubscription:
        """
        Create a PayPal subscription.

        Args:
            plan_id: PayPal billing plan ID
            subscriber_email: Subscriber email address
            return_url: URL to redirect after approval
            cancel_url: URL to redirect on cancel

        Returns:
            PayPalSubscription with subscription_id
        """
        if not self.enabled:
            return PayPalSubscription(
                subscription_id="MOCK-SUB-001",
                status="APPROVAL_PENDING",
                plan_id=plan_id,
            )

        token = await self._get_access_token()

        subscription_data = {
            "plan_id": plan_id,
            "subscriber": {
                "email_address": subscriber_email,
            },
            "application_context": {
                "brand_name": "AgentVoiceBox",
                "return_url": return_url,
                "cancel_url": cancel_url,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/billing/subscriptions",
                json=subscription_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            return PayPalSubscription(
                subscription_id=data["id"],
                status=data["status"],
                plan_id=plan_id,
            )

    async def cancel_subscription(self, subscription_id: str, reason: str = "") -> bool:
        """
        Cancel a PayPal subscription.

        Args:
            subscription_id: PayPal subscription ID
            reason: Cancellation reason

        Returns:
            True if cancelled successfully
        """
        if not self.enabled:
            return True

        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
                json={"reason": reason},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            return response.status_code == 204

    async def verify_webhook(
        self,
        transmission_id: str,
        transmission_time: str,
        cert_url: str,
        auth_algo: str,
        transmission_sig: str,
        webhook_event: dict,
    ) -> bool:
        """
        Verify a PayPal webhook signature.

        Args:
            transmission_id: PayPal-Transmission-Id header
            transmission_time: PayPal-Transmission-Time header
            cert_url: PayPal-Cert-Url header
            auth_algo: PayPal-Auth-Algo header
            transmission_sig: PayPal-Transmission-Sig header
            webhook_event: Webhook event body

        Returns:
            True if webhook signature is valid
        """
        if not self.enabled:
            return True

        token = await self._get_access_token()

        verify_data = {
            "transmission_id": transmission_id,
            "transmission_time": transmission_time,
            "cert_url": cert_url,
            "auth_algo": auth_algo,
            "transmission_sig": transmission_sig,
            "webhook_id": self.webhook_id,
            "webhook_event": webhook_event,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/notifications/verify-webhook-signature",
                json=verify_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            return data.get("verification_status") == "SUCCESS"


# Singleton instance
paypal_client = PayPalClient()

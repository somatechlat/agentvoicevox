"""
Notification Workflow Activities
================================

This module defines a set of Temporal Workflow Activities for sending various
types of notifications to users or tenants. It supports multiple communication
channels, including in-app notifications (via WebSockets), email, and webhooks,
orchestrating interactions with local database models, Django's email system,
and external HTTP services.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class NotificationRequest:
    """
    Defines the parameters for requesting a notification to be sent.

    Attributes:
        tenant_id (str): The ID of the tenant to whom the notification is relevant.
        user_id (Optional[str]): The ID of the specific user to notify. If None, it might be a tenant-wide notification.
        notification_type (str): The category/severity of the notification (e.g., 'info', 'warning', 'error', 'success').
        title (str): The title or subject of the notification.
        message (str): The main content of the notification.
        channel (str): The desired communication channel (e.g., 'in_app', 'email', 'webhook').
        metadata (Optional[dict[str, Any]]): Additional, unstructured metadata for the notification.
    """

    tenant_id: str
    user_id: Optional[str]
    notification_type: str
    title: str
    message: str
    channel: str = "in_app"
    metadata: Optional[dict[str, Any]] = None


@dataclass
class NotificationResult:
    """
    Represents the structured result of attempting to send a notification.

    Attributes:
        success (bool): True if the notification was sent successfully, False otherwise.
        notification_id (Optional[str]): The ID of the created notification record (e.g., in-app), if applicable.
        channel (str): The channel through which the notification was attempted.
        error (Optional[str]): An error message if the sending failed.
    """

    success: bool
    notification_id: Optional[str]
    channel: str
    error: Optional[str] = None


class NotificationActivities:
    """
    A collection of Temporal Workflow Activities for sending notifications.

    These activities provide robust and fault-tolerant mechanisms for
    delivering alerts and messages through various integrated channels.
    """

    @activity.defn(name="notification_send")
    async def send_notification(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """
        Dispatches a notification to the appropriate channel handler based on the request.

        This activity acts as a central point for sending notifications,
        delegating the actual sending logic to private, channel-specific methods.

        Args:
            request: A `NotificationRequest` dataclass instance with notification details.

        Returns:
            A `NotificationResult` object indicating the outcome of the sending attempt.
        """
        try:
            if request.channel == "in_app":
                return await self._send_in_app(request)
            elif request.channel == "email":
                return await self._send_email(request)
            elif request.channel == "webhook":
                return await self._send_webhook(request)
            else:
                return NotificationResult(
                    success=False,
                    notification_id=None,
                    channel=request.channel,
                    error=f"Unknown notification channel: {request.channel}",
                )

        except Exception as e:
            logger.error(
                f"Failed to send notification via channel {request.channel} for tenant {request.tenant_id}: {e}"
            )
            return NotificationResult(
                success=False,
                notification_id=None,
                channel=request.channel,
                error=str(e),
            )

    async def _send_in_app(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """
        Internal helper to send an in-app notification.

        This involves creating a `Notification` model entry and
        broadcasting it via Django Channels (WebSockets) to relevant clients.
        """
        # Local imports to avoid module-level dependencies.
        from apps.notifications.models import Notification
        from apps.tenants.models import Tenant

        try:
            tenant = await Tenant.objects.aget(id=request.tenant_id)
        except Tenant.DoesNotExist:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="in_app",
                error=f"Tenant {request.tenant_id} not found for in-app notification.",
            )

        # Create a database record for the in-app notification.
        notification = await Notification.objects.acreate(
            tenant=tenant,
            user_id=request.user_id,
            notification_type=request.notification_type,
            title=request.title,
            message=request.message,
            metadata=request.metadata or {},
        )

        # Attempt to broadcast the notification via WebSocket.
        from channels.layers import get_channel_layer  # Local import.

        channel_layer = get_channel_layer()
        if channel_layer:
            # Determine the WebSocket group to send to.
            if request.user_id:
                group_name = f"user_{request.user_id}_notifications"
            else:
                group_name = f"tenant_{request.tenant_id}_notifications"

            await channel_layer.group_send(
                group_name,
                {
                    "type": "notification.message",
                    "notification": {
                        "id": str(notification.id),
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "created_at": notification.created_at.isoformat(),
                        "metadata": notification.metadata,
                    },
                },
            )

        logger.info(
            f"Sent in-app notification to tenant {request.tenant_id} (user: {request.user_id})."
        )

        return NotificationResult(
            success=True,
            notification_id=str(notification.id),
            channel="in_app",
        )

    async def _send_email(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """
        Internal helper to send an email notification.

        Retrieves the user's email address and uses Django's mail functionality.
        Requires a `user_id` in the request.
        """
        if not request.user_id:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="email",
                error="User ID is required for email notifications.",
            )

        # Local imports.
        from apps.users.models import User
        from django.conf import settings
        from django.core.mail import send_mail

        try:
            user = await User.objects.aget(id=request.user_id)
        except User.DoesNotExist:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="email",
                error=f"User {request.user_id} not found for email notification.",
            )

        # Construct and send the email.
        send_mail(
            subject=request.title,
            message=request.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,  # Set to True in production to suppress errors.
        )

        logger.info(f"Sent email notification to user {user.email}.")

        return NotificationResult(
            success=True,
            notification_id=None,
            channel="email",
        )

    async def _send_webhook(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """
        Internal helper to send a webhook notification.

        This involves retrieving the tenant's webhook URL from `TenantSettings`
        and sending an HTTP POST request to that URL.
        """
        # Local imports.
        import httpx
        from apps.tenants.models import TenantSettings

        try:
            settings = await TenantSettings.objects.aget(tenant_id=request.tenant_id)
            webhook_url = settings.webhook_url
        except TenantSettings.DoesNotExist:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="webhook",
                error=f"Tenant settings for {request.tenant_id} not found.",
            )

        if not webhook_url:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="webhook",
                error="Webhook URL not configured for this tenant.",
            )

        # Send the HTTP POST request to the webhook URL.
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={
                    "type": request.notification_type,
                    "title": request.title,
                    "message": request.message,
                    "tenant_id": request.tenant_id,
                    "user_id": request.user_id,
                    "metadata": request.metadata,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=10.0,  # Timeout for the webhook request.
            )

            # Check for non-successful HTTP status codes.
            if response.status_code >= 400:
                return NotificationResult(
                    success=False,
                    notification_id=None,
                    channel="webhook",
                    error=f"Webhook call failed with status {response.status_code}.",
                )

        logger.info(f"Sent webhook notification to {webhook_url} for tenant {request.tenant_id}.")

        return NotificationResult(
            success=True,
            notification_id=None,
            channel="webhook",
        )

    @activity.defn(name="notification_send_bulk")
    async def send_bulk_notifications(
        self,
        tenant_id: str,
        user_ids: list[str],
        notification_type: str,
        title: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Sends notifications to a list of users within a specific tenant.

        This activity currently sends in-app notifications to each user.
        It aggregates results, reporting successes and failures.

        Args:
            tenant_id: The ID of the tenant.
            user_ids: A list of user IDs to send notifications to.
            notification_type: The category/severity of the notification.
            title: The title of the notification.
            message: The content of the notification.

        Returns:
            A dictionary summarizing the results, including total, success,
            failed counts, and specific errors for failed notifications.
        """
        results = {
            "total": len(user_ids),
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for user_id in user_ids:
            # Create a notification request for each user (currently hardcoded to in_app).
            request = NotificationRequest(
                tenant_id=tenant_id,
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                channel="in_app",  # Bulk notifications currently only support in-app.
            )

            # Send individual notification and record the result.
            result = await self.send_notification(request)

            if result.success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "user_id": user_id,
                        "error": result.error,
                    }
                )

        logger.info(
            f"Sent bulk notifications: {results['success']}/{results['total']} succeeded for tenant {tenant_id}."
        )

        return results

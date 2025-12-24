"""
Notification activities for Temporal workflows.

Handles sending notifications via various channels.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class NotificationRequest:
    """Request to send a notification."""

    tenant_id: str
    user_id: Optional[str]
    notification_type: str  # info, warning, error, success
    title: str
    message: str
    channel: str = "in_app"  # in_app, email, webhook
    metadata: Dict[str, Any] = None


@dataclass
class NotificationResult:
    """Result of sending a notification."""

    success: bool
    notification_id: Optional[str]
    channel: str
    error: Optional[str] = None


class NotificationActivities:
    """
    Notification activities for sending alerts and messages.

    Activities:
    - send_notification: Send a notification
    - send_bulk_notifications: Send notifications to multiple users
    - send_webhook: Send webhook notification
    """

    @activity.defn(name="notification_send")
    async def send_notification(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """
        Send a notification to a user or tenant.

        Args:
            request: NotificationRequest with notification details

        Returns:
            NotificationResult with send status
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
                    error=f"Unknown channel: {request.channel}",
                )

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
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
        """Send in-app notification."""
        from apps.notifications.models import Notification
        from apps.tenants.models import Tenant

        tenant = await Tenant.objects.aget(id=request.tenant_id)

        notification = await Notification.objects.acreate(
            tenant=tenant,
            user_id=request.user_id,
            notification_type=request.notification_type,
            title=request.title,
            message=request.message,
            metadata=request.metadata or {},
        )

        # Broadcast via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"tenant_{request.tenant_id}_notifications"
            if request.user_id:
                group_name = f"user_{request.user_id}_notifications"

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
                    },
                },
            )

        logger.info(
            f"Sent in-app notification to tenant {request.tenant_id}"
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
        """Send email notification."""
        from django.core.mail import send_mail
        from django.conf import settings

        if not request.user_id:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="email",
                error="User ID required for email notifications",
            )

        from apps.users.models import User

        try:
            user = await User.objects.aget(id=request.user_id)
        except User.DoesNotExist:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="email",
                error="User not found",
            )

        # Send email
        send_mail(
            subject=request.title,
            message=request.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Sent email notification to {user.email}")

        return NotificationResult(
            success=True,
            notification_id=None,
            channel="email",
        )

    async def _send_webhook(
        self,
        request: NotificationRequest,
    ) -> NotificationResult:
        """Send webhook notification."""
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
                error="Tenant settings not found",
            )

        if not webhook_url:
            return NotificationResult(
                success=False,
                notification_id=None,
                channel="webhook",
                error="Webhook URL not configured",
            )

        # Send webhook
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
                timeout=10.0,
            )

            if response.status_code >= 400:
                return NotificationResult(
                    success=False,
                    notification_id=None,
                    channel="webhook",
                    error=f"Webhook returned {response.status_code}",
                )

        logger.info(f"Sent webhook notification to {webhook_url}")

        return NotificationResult(
            success=True,
            notification_id=None,
            channel="webhook",
        )

    @activity.defn(name="notification_send_bulk")
    async def send_bulk_notifications(
        self,
        tenant_id: str,
        user_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send notifications to multiple users.

        Args:
            tenant_id: Tenant identifier
            user_ids: List of user IDs
            notification_type: Type of notification
            title: Notification title
            message: Notification message

        Returns:
            Dict with send results
        """
        results = {
            "total": len(user_ids),
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for user_id in user_ids:
            request = NotificationRequest(
                tenant_id=tenant_id,
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                channel="in_app",
            )

            result = await self.send_notification(request)

            if result.success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user_id,
                    "error": result.error,
                })

        logger.info(
            f"Sent bulk notifications: {results['success']}/{results['total']} succeeded"
        )

        return results

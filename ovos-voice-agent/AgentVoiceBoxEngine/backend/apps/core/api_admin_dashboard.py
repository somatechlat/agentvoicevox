"""
System Administration Dashboard API Endpoints
=============================================

This module provides API endpoints specifically designed for the system
administrator's dashboard. These endpoints aggregate key operational metrics
and health indicators from across the platform, offering a high-level overview
of tenant activity, resource usage, and system status.

Access to all endpoints in this module is strictly restricted to users with
the `SYSADMIN` role.
"""


from django.db.models import Sum
from django.utils import timezone
from ninja import Router

from apps.billing.models import UsageEvent
from apps.core.exceptions import PermissionDeniedError
from apps.tenants.models import Tenant

# Router for admin dashboard endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Admin - Dashboard"])


def require_sysadmin(request):
    """
    Checks if the requesting user has the 'sysadmin' role.

    This function serves as a dependency for admin dashboard endpoints,
    ensuring only system administrators can access these critical metrics.

    Args:
        request: The incoming HttpRequest object.

    Raises:
        PermissionDeniedError: If the user is not a system administrator.
    """
    roles = getattr(request, "jwt_roles", [])
    if "sysadmin" not in roles:
        raise PermissionDeniedError("SYSADMIN role required")


@router.get("/dashboard", summary="Get Admin Dashboard Metrics (SysAdmin)")
def admin_dashboard(request, period: str = "7d"):
    """
    Retrieves a comprehensive set of operational metrics and health indicators
    for the entire platform.

    Metrics include tenant counts, API request volumes, audio usage, and top tenants.
    Some metrics are currently placeholders or derived from mock data.

    **Permissions:** Requires SYSADMIN role.

    Args:
        period: (str, currently unused) The desired aggregation period for metrics (e.g., '7d', '30d').
                The current implementation calculates metrics for 'today' and 'this month' regardless of this parameter.

    Returns:
        A dictionary containing aggregated metrics, health status, and top tenant data.
    """
    require_sysadmin(request)

    now = timezone.now()
    # Calculate start of the current month and day for metric aggregation.
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Tenant-related metrics
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status=Tenant.Status.ACTIVE).count()
    new_tenants = Tenant.objects.filter(created_at__gte=month_start).count()

    # Aggregate API requests for today.
    api_requests_today = (
        UsageEvent.all_objects.filter(
            event_type=UsageEvent.EventType.API_CALL,
            created_at__gte=day_start,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    # Aggregate audio minutes for today.
    audio_minutes_today = (
        UsageEvent.all_objects.filter(
            event_type=UsageEvent.EventType.AUDIO_MINUTES,
            created_at__gte=day_start,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    # Retrieve top 10 tenants (for demonstration, API requests are for today).
    top_tenants = []
    # This loop potentially causes N+1 query issues if UsageEvent.all_objects is used inside.
    # For now, limited to 10 tenants.
    for tenant in Tenant.objects.all().order_by("-created_at")[:10]:
        tenant_api_requests = (
            UsageEvent.all_objects.filter(
                tenant=tenant,
                event_type=UsageEvent.EventType.API_CALL,
                created_at__gte=day_start,
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        top_tenants.append(
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "plan": tenant.tier,
                "mrr_cents": 0,  # Placeholder for actual MRR calculation.
                "api_requests_today": int(tenant_api_requests),
            }
        )

    return {
        "metrics": {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "total_mrr_cents": 0,  # Placeholder for Total Monthly Recurring Revenue.
            "total_api_requests_today": int(api_requests_today),
            "total_audio_minutes_today": float(audio_minutes_today),
            "new_tenants_this_month": new_tenants,
            "churn_rate_percent": 0,  # Placeholder for tenant churn rate.
        },
        "health": {
            "overall": "ok",  # System health status (e.g., from monitoring systems).
            "services": {},  # Detailed status of individual services.
            "alerts": [],  # Active alerts or warnings.
        },
        "top_tenants": top_tenants,
    }

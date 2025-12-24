"""
Django Ninja API configuration.

This module configures the main API instance and registers all routers.
"""
from ninja import NinjaAPI
from ninja.errors import ValidationError as NinjaValidationError

from apps.core.exceptions import APIException

# ==========================================================================
# API INSTANCE
# ==========================================================================
api = NinjaAPI(
    title="AgentVoiceBox API",
    version="2.0.0",
    description="Enterprise Voice Agent Platform API",
    docs_url="/docs",
    openapi_url="/openapi.json",
)


# ==========================================================================
# EXCEPTION HANDLERS
# ==========================================================================
@api.exception_handler(APIException)
def handle_api_exception(request, exc: APIException):
    """Handle custom API exceptions."""
    return api.create_response(
        request,
        {
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
        status=exc.status_code,
    )


@api.exception_handler(NinjaValidationError)
def handle_validation_error(request, exc: NinjaValidationError):
    """Handle Pydantic validation errors."""
    return api.create_response(
        request,
        {
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors,
        },
        status=400,
    )


# ==========================================================================
# REGISTER ROUTERS
# ==========================================================================
def register_routers():
    """Register all API routers."""
    from apps.api_keys.api import router as api_keys_router
    from apps.audit.api import router as audit_router
    from apps.billing.api import router as billing_router
    from apps.notifications.api import router as notifications_router
    from apps.projects.api import router as projects_router
    from apps.sessions.api import router as sessions_router
    from apps.tenants.api import router as tenants_router
    from apps.tenants.api_admin import router as admin_tenants_router
    from apps.themes.api import router as themes_router
    from apps.users.api import router as users_router
    from apps.users.api_admin import router as admin_users_router
    from apps.voice.api import router as voice_router

    # Public routers
    api.add_router("/tenants", tenants_router, tags=["Tenants"])
    api.add_router("/users", users_router, tags=["Users"])
    api.add_router("/projects", projects_router, tags=["Projects"])
    api.add_router("/api-keys", api_keys_router, tags=["API Keys"])
    api.add_router("/sessions", sessions_router, tags=["Sessions"])
    api.add_router("/billing", billing_router, tags=["Billing"])
    api.add_router("/voice", voice_router, tags=["Voice"])
    api.add_router("/themes", themes_router, tags=["Themes"])
    api.add_router("/audit", audit_router, tags=["Audit"])
    api.add_router("/notifications", notifications_router, tags=["Notifications"])

    # Admin routers (SYSADMIN only)
    api.add_router("/admin/tenants", admin_tenants_router, tags=["Admin - Tenants"])
    api.add_router("/admin/users", admin_users_router, tags=["Admin - Users"])


# Register routers on module load
register_routers()

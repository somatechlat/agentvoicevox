"""
Central API Configuration for Django Ninja
==========================================

This module serves as the primary configuration entry point for the entire
Django Ninja API. It initializes the global `NinjaAPI` instance, sets up
centralized exception handlers for consistent error responses, and registers
all API routers from various application modules.

The `api` object defined here is the single point of entry for all API requests
and is typically integrated into Django's URL routing.
"""

from ninja import NinjaAPI
from ninja.errors import ValidationError as NinjaValidationError

from apps.core.exceptions import APIException

# ==========================================================================
# API INSTANCE INITIALIZATION
# ==========================================================================
api = NinjaAPI(
    title="AgentVoiceBox API",
    version="2.0.0",
    description="The Enterprise Voice Agent Platform API provides programmatic access to manage tenants, users, projects, API keys, voice configurations, and real-time voice sessions.",
    docs_url="/docs",  # Endpoint for the OpenAPI (Swagger UI) documentation.
    openapi_url="/openapi.json",  # Endpoint for the OpenAPI specification (JSON).
)


# ==========================================================================
# GLOBAL EXCEPTION HANDLERS
# ==========================================================================
@api.exception_handler(APIException)
def handle_api_exception(request, exc: APIException):
    """
    Handles custom `APIException` instances, translating them into standardized
    JSON error responses with appropriate HTTP status codes.

    This ensures that all custom exceptions raised across the API surface return
    a consistent error structure to clients.
    """
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
    """
    Handles Pydantic `NinjaValidationError`s, which occur when incoming request
    data (payloads, query parameters) do not conform to the defined schemas.
    Translates them into a standardized HTTP 400 Bad Request response.
    """
    return api.create_response(
        request,
        {
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors,  # Pydantic's detailed validation errors.
        },
        status=400,
    )


# ==========================================================================
# ROUTER REGISTRATION
# ==========================================================================
def register_routers():
    """
    Imports and registers all API routers with the main NinjaAPI instance.

    Routers are grouped by functionality (e.g., Tenants, Users, Projects) and
    categorized as either public (tenant-scoped) or admin (SYSADMIN-only)
    for clear documentation and access control. This centralized registration
    also helps manage potential circular import issues between apps.
    """
    # Import routers from various apps.
    # Public (Tenant-Scoped) Routers
    from apps.api_keys.api import router as api_keys_router
    from apps.audit.api import router as audit_router
    from apps.billing.api import router as billing_router

    # Admin (SYSADMIN-only) Routers
    from apps.core.api_admin_dashboard import router as admin_dashboard_router
    from apps.llm.api import router as llm_router
    from apps.notifications.api import router as notifications_router
    from apps.projects.api import router as projects_router
    from apps.sessions.api import router as sessions_router
    from apps.stt.api import router as stt_router
    from apps.tenants.api import router as tenants_router
    from apps.tenants.api_admin import router as admin_tenants_router
    from apps.tenants.api_onboarding import router as onboarding_router
    from apps.themes.api import router as themes_router
    from apps.users.api import router as users_router
    from apps.users.api_admin import router as admin_users_router
    from apps.users.api_profile import router as profile_router
    from apps.voice.api import router as voice_router
    from apps.voice.api_voice_cloning import router as voice_cloning_router
    from apps.voice.api_wake_words import router as wake_words_router

    # Register Public (Tenant-Scoped) Routers
    api.add_router("/tenants", tenants_router, tags=["Tenants"])
    api.add_router("/onboarding", onboarding_router, tags=["Onboarding"])
    api.add_router("/users", users_router, tags=["Users"])
    api.add_router(
        "/user", profile_router, tags=["User Profile"]
    )  # Renamed tag for clarity
    api.add_router("/projects", projects_router, tags=["Projects"])
    api.add_router("/api-keys", api_keys_router, tags=["API Keys"])
    api.add_router("/sessions", sessions_router, tags=["Sessions"])
    api.add_router("/billing", billing_router, tags=["Billing"])
    api.add_router(
        "/voice", voice_router, tags=["Voice Personas & Models"]
    )  # Renamed tag for clarity
    api.add_router("/voice-cloning", voice_cloning_router, tags=["Voice Cloning"])
    api.add_router("/wake-words", wake_words_router, tags=["Wake Words"])
    api.add_router(
        "/llm", llm_router, tags=["LLM Integrations"]
    )  # Renamed tag for clarity
    api.add_router(
        "/stt", stt_router, tags=["STT Integrations"]
    )  # Renamed tag for clarity
    api.add_router("/themes", themes_router, tags=["Themes"])
    api.add_router(
        "/audit", audit_router, tags=["Audit Logs"]
    )  # Renamed tag for clarity
    api.add_router("/notifications", notifications_router, tags=["Notifications"])

    # Register Admin (SYSADMIN-only) Routers
    api.add_router("/admin/tenants", admin_tenants_router, tags=["Admin - Tenants"])
    api.add_router("/admin/users", admin_users_router, tags=["Admin - Users"])
    api.add_router("/admin", admin_dashboard_router, tags=["Admin - Dashboard"])


# Execute router registration on module load to ensure all endpoints are configured.
register_routers()

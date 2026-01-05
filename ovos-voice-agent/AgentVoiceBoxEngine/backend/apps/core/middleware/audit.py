"""
Audit logging middleware.

Automatically logs all write operations (POST, PUT, PATCH, DELETE)
to auditable paths.
"""

from django.http import HttpRequest, HttpResponse

# Paths to audit
AUDITABLE_PATHS = [
    "/api/v2/tenants",
    "/api/v2/users",
    "/api/v2/projects",
    "/api/v2/api-keys",
    "/api/v2/sessions",
    "/api/v2/billing",
    "/api/v2/voice",
    "/api/v2/themes",
    "/api/v2/admin",
]

# Methods to audit
AUDITABLE_METHODS = ["POST", "PUT", "PATCH", "DELETE"]


class AuditMiddleware:
    """Middleware for automatic audit logging."""

    def __init__(self, get_response):
        """Initializes the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Processes the request and creates an audit log if necessary."""
        # Process request
        response = self.get_response(request)

        # Check if this request should be audited
        if self._should_audit(request, response):
            self._create_audit_log(request, response)

        return response

    def _should_audit(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Check if request should be audited."""
        # Only audit write methods
        if request.method not in AUDITABLE_METHODS:
            return False

        # Only audit successful requests
        if response.status_code >= 400:
            return False

        # Check if path is auditable
        for path in AUDITABLE_PATHS:
            if request.path.startswith(path):
                return True

        return False

    def _create_audit_log(self, request: HttpRequest, response: HttpResponse) -> None:
        """Create audit log entry."""
        from apps.audit.models import AuditLog

        try:
            # Determine action from method
            action_map = {
                "POST": "create",
                "PUT": "update",
                "PATCH": "update",
                "DELETE": "delete",
            }
            action = action_map.get(request.method, "api_call")

            # Extract resource info from path
            resource_type, resource_id = self._extract_resource_info(request.path)

            # Get actor info
            actor_id = getattr(request, "user_id", None) or getattr(request, "api_key_id", None)
            actor_type = "api_key" if hasattr(request, "api_key_id") else "user"
            actor_email = getattr(request, "jwt_claims", {}).get("email", "")

            # Get tenant
            tenant_id = getattr(request, "tenant_id", None)

            # Create audit log
            AuditLog.log(
                tenant_id=tenant_id,
                actor_id=str(actor_id) if actor_id else "anonymous",
                actor_email=actor_email,
                actor_type=actor_type,
                ip_address=self._get_client_ip(request),
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=f"{request.method} {request.path}",
            )
        except Exception:
            # Don't fail request if audit logging fails
            pass

    def _extract_resource_info(self, path: str) -> tuple:
        """Extract resource type and ID from path."""
        parts = path.strip("/").split("/")

        # /api/v2/resource/id -> resource, id
        if len(parts) >= 3:
            resource_type = parts[2]  # e.g., "tenants", "users"
            resource_id = parts[3] if len(parts) > 3 else ""
            return resource_type, resource_id

        return "unknown", ""

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

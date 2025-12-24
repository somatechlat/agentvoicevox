"""
Tenant middleware for multi-tenancy support.

Extracts tenant context from:
1. JWT claims (tenant_id)
2. X-Tenant-ID header
3. Subdomain

Sets tenant in thread-local storage accessible via get_current_tenant().
"""
import threading
from typing import Optional
from uuid import UUID

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings

# Thread-local storage for tenant context
_tenant_context = threading.local()


def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_tenant_context, "tenant", None)


def get_current_tenant_id() -> Optional[UUID]:
    """Get the current tenant ID from thread-local storage."""
    return getattr(_tenant_context, "tenant_id", None)


def set_current_tenant(tenant) -> None:
    """Set the current tenant in thread-local storage."""
    _tenant_context.tenant = tenant
    _tenant_context.tenant_id = tenant.id if tenant else None


def set_current_tenant_id(tenant_id: Optional[UUID]) -> None:
    """Set the current tenant ID in thread-local storage."""
    _tenant_context.tenant_id = tenant_id


def clear_current_tenant() -> None:
    """Clear the current tenant from thread-local storage."""
    _tenant_context.tenant = None
    _tenant_context.tenant_id = None


# Paths that don't require tenant context
TENANT_EXEMPT_PATHS = [
    "/health/",
    "/metrics",
    "/api/v2/docs",
    "/api/v2/openapi.json",
    "/admin/",
]


class TenantMiddleware:
    """Middleware for extracting and validating tenant context."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Clear any existing tenant context
        clear_current_tenant()
        
        # Skip tenant check for exempt paths
        if self._is_exempt_path(request.path):
            return self.get_response(request)
        
        # Try to extract tenant ID from various sources
        tenant_id = self._extract_tenant_id(request)
        
        if tenant_id:
            # Validate and load tenant
            tenant = self._load_tenant(tenant_id)
            
            if tenant is None:
                return JsonResponse(
                    {
                        "error": "tenant_not_found",
                        "message": "Tenant not found",
                    },
                    status=404,
                )
            
            if tenant.status == "suspended":
                return JsonResponse(
                    {
                        "error": "tenant_suspended",
                        "message": "Tenant account is suspended",
                    },
                    status=403,
                )
            
            if tenant.status == "deleted":
                return JsonResponse(
                    {
                        "error": "tenant_not_found",
                        "message": "Tenant not found",
                    },
                    status=404,
                )
            
            # Set tenant context
            set_current_tenant(tenant)
            request.tenant = tenant
            request.tenant_id = tenant.id
        
        # Process request
        response = self.get_response(request)
        
        # Clear tenant context after request
        clear_current_tenant()
        
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tenant requirement."""
        for exempt_path in TENANT_EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _extract_tenant_id(self, request: HttpRequest) -> Optional[UUID]:
        """Extract tenant ID from request."""
        # 1. From JWT claims (set by auth middleware)
        jwt_tenant_id = getattr(request, "jwt_tenant_id", None)
        if jwt_tenant_id:
            try:
                return UUID(jwt_tenant_id)
            except (ValueError, TypeError):
                pass
        
        # 2. From X-Tenant-ID header
        header_tenant_id = request.headers.get("X-Tenant-ID")
        if header_tenant_id:
            try:
                return UUID(header_tenant_id)
            except (ValueError, TypeError):
                pass
        
        # 3. From subdomain
        host = request.get_host().split(":")[0]
        parts = host.split(".")
        if len(parts) > 2:
            subdomain = parts[0]
            tenant = self._load_tenant_by_slug(subdomain)
            if tenant:
                return tenant.id
        
        return None
    
    def _load_tenant(self, tenant_id: UUID):
        """Load tenant by ID from database."""
        from apps.tenants.models import Tenant
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None
    
    def _load_tenant_by_slug(self, slug: str):
        """Load tenant by slug from database."""
        from apps.tenants.models import Tenant
        try:
            return Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return None

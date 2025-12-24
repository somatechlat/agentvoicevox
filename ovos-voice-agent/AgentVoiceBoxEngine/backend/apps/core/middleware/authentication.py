"""
Keycloak authentication middleware.

Validates JWT tokens from Authorization header.
Extracts user_id (sub), tenant_id, and roles from JWT claims.
Supports API key authentication via X-API-Key header.
"""
import jwt
import requests
from typing import Optional, Dict, Any
from functools import lru_cache

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache

# Paths that don't require authentication
AUTH_EXEMPT_PATHS = [
    "/health/",
    "/metrics",
    "/api/v2/docs",
    "/api/v2/openapi.json",
]


class KeycloakAuthenticationMiddleware:
    """Middleware for JWT and API key authentication."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.keycloak_config = settings.KEYCLOAK
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip auth for exempt paths
        if self._is_exempt_path(request.path):
            return self.get_response(request)
        
        # Try JWT authentication first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            result = self._validate_jwt(token)
            
            if result.get("error"):
                return JsonResponse(
                    {
                        "error": result["error"],
                        "message": result["message"],
                    },
                    status=401,
                )
            
            # Set user context on request
            request.user_id = result.get("user_id")
            request.jwt_tenant_id = result.get("tenant_id")
            request.jwt_roles = result.get("roles", [])
            request.jwt_claims = result.get("claims", {})
            request.auth_type = "jwt"
            
            # Create or update user record
            self._sync_user(result)
        
        # Try API key authentication
        elif api_key := request.headers.get("X-API-Key"):
            result = self._validate_api_key(api_key, request)
            
            if result.get("error"):
                return JsonResponse(
                    {
                        "error": result["error"],
                        "message": result["message"],
                    },
                    status=401,
                )
            
            # Set API key context on request
            request.user_id = result.get("user_id")
            request.jwt_tenant_id = result.get("tenant_id")
            request.api_key_id = result.get("api_key_id")
            request.api_key_scopes = result.get("scopes", [])
            request.auth_type = "api_key"
        
        return self.get_response(request)
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from authentication."""
        for exempt_path in AUTH_EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _validate_jwt(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and extract claims."""
        try:
            # Get Keycloak public key
            public_key = self._get_keycloak_public_key()
            
            # Decode and validate token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=self.keycloak_config["ALGORITHMS"],
                audience=self.keycloak_config["AUDIENCE"],
                options={"verify_exp": True},
            )
            
            return {
                "user_id": claims.get("sub"),
                "tenant_id": claims.get("tenant_id"),
                "email": claims.get("email"),
                "first_name": claims.get("given_name"),
                "last_name": claims.get("family_name"),
                "roles": claims.get("realm_access", {}).get("roles", []),
                "claims": claims,
            }
        
        except jwt.ExpiredSignatureError:
            return {"error": "token_expired", "message": "Token has expired"}
        except jwt.InvalidTokenError as e:
            return {"error": "invalid_token", "message": f"Invalid token: {str(e)}"}
        except Exception as e:
            return {"error": "authentication_error", "message": str(e)}
    
    def _get_keycloak_public_key(self) -> str:
        """Fetch and cache Keycloak public key."""
        cache_key = "keycloak_public_key"
        public_key = cache.get(cache_key)
        
        if not public_key:
            # Fetch from Keycloak
            url = f"{self.keycloak_config['URL']}/realms/{self.keycloak_config['REALM']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            realm_info = response.json()
            public_key_raw = realm_info["public_key"]
            
            # Format as PEM
            public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key_raw}\n-----END PUBLIC KEY-----"
            
            # Cache for 1 hour
            cache.set(cache_key, public_key, timeout=3600)
        
        return public_key
    
    def _validate_api_key(self, api_key: str, request: HttpRequest) -> Dict[str, Any]:
        """Validate API key and return key data."""
        from apps.api_keys.services import APIKeyService
        
        try:
            key_data = APIKeyService.validate_key(
                api_key,
                ip_address=self._get_client_ip(request),
            )
            return key_data
        except Exception as e:
            error_code = getattr(e, "error_code", "authentication_error")
            return {"error": error_code, "message": str(e)}
    
    def _sync_user(self, jwt_data: Dict[str, Any]) -> None:
        """Create or update user from JWT claims."""
        from apps.users.services import UserService
        
        try:
            UserService.sync_from_jwt(jwt_data)
        except Exception:
            # Log but don't fail request
            pass
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

"""
AuthBearer class for Django Ninja authentication.

Validates JWT tokens and API keys, attaching user context to request.auth.
"""

import logging
from typing import Any, Optional

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)


class AuthBearer(HttpBearer):
    """
    JWT/API Key authentication for Django Ninja endpoints.

    Validates tokens and attaches user context to request.auth.

    Usage:
        from ninja import NinjaAPI
        from apps.core.permissions import AuthBearer

        api = NinjaAPI(auth=AuthBearer())

        @api.get("/protected")
        def protected_endpoint(request):
            user_context = request.auth
            # user_context contains: user_id, tenant_id, roles, etc.
    """

    def authenticate(self, request, token: str) -> Optional[dict[str, Any]]:
        """
        Authenticate request using JWT token or API key.

        Args:
            request: The HTTP request
            token: The token from Authorization header

        Returns:
            User context dict on success, None on failure.
            Context includes: user_id, tenant_id, roles, auth_type, etc.
        """
        # Try JWT authentication
        if self._is_jwt_token(token):
            return self._validate_jwt(request, token)

        # Try API key authentication
        return self._validate_api_key(request, token)

    def _is_jwt_token(self, token: str) -> bool:
        """Check if token looks like a JWT (has 3 parts separated by dots)."""
        return token.count(".") == 2

    def _validate_jwt(self, request, token: str) -> Optional[dict[str, Any]]:
        """
        Validate JWT token and return user context.

        Args:
            request: The HTTP request
            token: The JWT token

        Returns:
            User context dict or None if validation fails
        """
        try:
            # Get cached public key
            public_key = self._get_keycloak_public_key()

            keycloak_config = getattr(settings, "KEYCLOAK", {})

            # Decode and validate
            claims = jwt.decode(
                token,
                public_key,
                algorithms=keycloak_config.get("ALGORITHMS", ["RS256"]),
                audience=keycloak_config.get("AUDIENCE", "agentvoicebox-backend"),
                options={"verify_exp": True},
            )

            # Extract roles from realm_access or resource_access
            roles = []
            if "realm_access" in claims:
                roles.extend(claims["realm_access"].get("roles", []))
            if "resource_access" in claims:
                for resource, access in claims["resource_access"].items():
                    roles.extend(access.get("roles", []))

            # Build user context
            context = {
                "user_id": claims.get("sub"),
                "tenant_id": claims.get("tenant_id"),
                "email": claims.get("email"),
                "first_name": claims.get("given_name"),
                "last_name": claims.get("family_name"),
                "roles": list(set(roles)),  # Deduplicate
                "auth_type": "jwt",
                "claims": claims,
            }

            logger.debug(
                f"JWT authenticated: user_id={context['user_id']} "
                f"tenant_id={context['tenant_id']} roles={context['roles']}"
            )

            return context

        except jwt.ExpiredSignatureError:
            logger.warning("JWT authentication failed: token expired")
            return None
        except jwt.InvalidAudienceError:
            logger.warning("JWT authentication failed: invalid audience")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT authentication failed: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return None

    def _validate_api_key(self, request, token: str) -> Optional[dict[str, Any]]:
        """
        Validate API key and return user context.

        Args:
            request: The HTTP request
            token: The API key

        Returns:
            User context dict or None if validation fails
        """
        try:
            from apps.api_keys.services import APIKeyService

            key_data = APIKeyService.validate_key(
                token,
                ip_address=self._get_client_ip(request),
            )

            context = {
                "user_id": key_data.get("user_id"),
                "tenant_id": key_data.get("tenant_id"),
                "api_key_id": key_data.get("api_key_id"),
                "scopes": key_data.get("scopes", []),
                "auth_type": "api_key",
            }

            logger.debug(
                f"API key authenticated: api_key_id={context['api_key_id']} "
                f"tenant_id={context['tenant_id']}"
            )

            return context

        except Exception as e:
            logger.warning(f"API key authentication failed: {e}")
            return None

    def _get_keycloak_public_key(self) -> str:
        """
        Fetch and cache Keycloak public key.

        Returns:
            PEM-formatted public key string

        Raises:
            Exception if unable to fetch public key
        """
        cache_key = "keycloak_public_key"
        public_key = cache.get(cache_key)

        if not public_key:
            keycloak_config = getattr(settings, "KEYCLOAK", {})
            missing = [key for key in ("URL", "REALM") if key not in keycloak_config]
            if missing:
                raise ValueError(
                    f"Keycloak configuration missing keys: {', '.join(missing)}"
                )

            url = keycloak_config["URL"]
            realm = keycloak_config["REALM"]

            realm_url = f"{url}/realms/{realm}"

            try:
                response = requests.get(realm_url, timeout=10)
                response.raise_for_status()

                realm_info = response.json()
                public_key_raw = realm_info["public_key"]

                # Format as PEM
                public_key = (
                    f"-----BEGIN PUBLIC KEY-----\n"
                    f"{public_key_raw}\n"
                    f"-----END PUBLIC KEY-----"
                )

                # Cache for 1 hour
                cache.set(cache_key, public_key, timeout=3600)

                logger.info("Keycloak public key fetched and cached")

            except requests.RequestException as e:
                logger.error(f"Failed to fetch Keycloak public key: {e}")
                raise

        return public_key

    def _get_client_ip(self, request) -> str:
        """
        Extract client IP from request.

        Args:
            request: The HTTP request

        Returns:
            Client IP address string
        """
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


class OptionalAuthBearer(AuthBearer):
    """
    Optional authentication - allows unauthenticated requests.

    Returns None for request.auth if no valid token is provided,
    but doesn't reject the request.

    Usage:
        @api.get("/public", auth=OptionalAuthBearer())
        def public_endpoint(request):
            if request.auth:
                # Authenticated user
                pass
            else:
                # Anonymous user
                pass
    """

    def authenticate(self, request, token: str) -> Optional[dict[str, Any]]:
        """
        Authenticate if token provided, otherwise return empty context.
        """
        if not token:
            return {}

        result = super().authenticate(request, token)
        return result if result else {}

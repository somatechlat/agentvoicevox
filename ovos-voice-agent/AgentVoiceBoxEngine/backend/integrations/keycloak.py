"""
Keycloak integration client.

Provides JWT validation and user management via Keycloak.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from django.conf import settings
from jwt import PyJWKClient
from jwt import decode as jwt_decode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


@dataclass
class KeycloakUser:
    """Keycloak user representation."""

    id: str
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    enabled: bool
    realm_roles: list[str]
    groups: list[str]
    attributes: dict[str, Any]


@dataclass
class TokenClaims:
    """Decoded JWT token claims."""

    sub: str  # User ID
    email: str
    email_verified: bool
    name: str
    given_name: str
    family_name: str
    preferred_username: str
    realm_access: dict[str, list[str]]
    resource_access: dict[str, dict[str, list[str]]]
    tenant_id: Optional[str]
    exp: int
    iat: int


class KeycloakClient:
    """
    Keycloak client for authentication and user management.

    Handles:
    - JWT token validation
    - Public key caching
    - User CRUD operations
    - Group management
    """

    def __init__(self):
        """Initialize Keycloak client from Django settings."""
        self.base_url = settings.KEYCLOAK["URL"]
        self.realm = settings.KEYCLOAK["REALM"]
        self.client_id = settings.KEYCLOAK["CLIENT_ID"]
        self.client_secret = settings.KEYCLOAK["CLIENT_SECRET"]
        self.algorithms = settings.KEYCLOAK["ALGORITHMS"]
        self.audience = settings.KEYCLOAK["AUDIENCE"]

        # Build URLs
        self.realm_url = f"{self.base_url}/realms/{self.realm}"
        self.token_url = f"{self.realm_url}/protocol/openid-connect/token"
        self.userinfo_url = f"{self.realm_url}/protocol/openid-connect/userinfo"
        self.jwks_url = f"{self.realm_url}/protocol/openid-connect/certs"
        self.admin_url = f"{self.base_url}/admin/realms/{self.realm}"

        # Initialize JWKS client
        self._jwks_client: Optional[PyJWKClient] = None
        self._admin_token: Optional[str] = None
        self._admin_token_expires: Optional[datetime] = None

    @property
    def jwks_client(self) -> PyJWKClient:
        """Get or create JWKS client."""
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)
        return self._jwks_client

    def validate_token(self, token: str) -> TokenClaims:
        """
        Validate a JWT token and return claims.

        Args:
            token: JWT access token

        Returns:
            Decoded token claims

        Raises:
            ExpiredSignatureError: If token is expired
            InvalidTokenError: If token is invalid
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate token
            payload = jwt_decode(
                token,
                signing_key.key,
                algorithms=self.algorithms,
                audience=self.audience,
                options={"verify_exp": True},
            )

            # Extract tenant_id from custom claim or groups
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                # Try to extract from groups
                groups = payload.get("groups", [])
                for group in groups:
                    if group.startswith("/tenants/"):
                        tenant_id = group.split("/")[-1]
                        break

            return TokenClaims(
                sub=payload["sub"],
                email=payload.get("email", ""),
                email_verified=payload.get("email_verified", False),
                name=payload.get("name", ""),
                given_name=payload.get("given_name", ""),
                family_name=payload.get("family_name", ""),
                preferred_username=payload.get("preferred_username", ""),
                realm_access=payload.get("realm_access", {}),
                resource_access=payload.get("resource_access", {}),
                tenant_id=tenant_id,
                exp=payload["exp"],
                iat=payload["iat"],
            )

        except ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    async def _get_admin_token(self) -> str:
        """Get admin access token for Keycloak Admin API."""
        # Check cache
        if self._admin_token and self._admin_token_expires:
            if datetime.utcnow() < self._admin_token_expires:
                return self._admin_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

            self._admin_token = data["access_token"]
            # Expire 60 seconds early to be safe
            expires_in = data.get("expires_in", 300) - 60
            self._admin_token_expires = datetime.utcnow() + timedelta(
                seconds=expires_in
            )

            return self._admin_token

    async def get_user(self, user_id: str) -> Optional[KeycloakUser]:
        """
        Get user by ID from Keycloak.

        Args:
            user_id: Keycloak user ID

        Returns:
            KeycloakUser or None if not found
        """
        token = await self._get_admin_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.admin_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            # Get user groups
            groups_response = await client.get(
                f"{self.admin_url}/users/{user_id}/groups",
                headers={"Authorization": f"Bearer {token}"},
            )
            groups = (
                [g["path"] for g in groups_response.json()]
                if groups_response.status_code == 200
                else []
            )

            # Get realm roles
            roles_response = await client.get(
                f"{self.admin_url}/users/{user_id}/role-mappings/realm",
                headers={"Authorization": f"Bearer {token}"},
            )
            roles = (
                [r["name"] for r in roles_response.json()]
                if roles_response.status_code == 200
                else []
            )

            return KeycloakUser(
                id=data["id"],
                email=data.get("email", ""),
                first_name=data.get("firstName", ""),
                last_name=data.get("lastName", ""),
                email_verified=data.get("emailVerified", False),
                enabled=data.get("enabled", True),
                realm_roles=roles,
                groups=groups,
                attributes=data.get("attributes", {}),
            )

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        tenant_id: str,
        enabled: bool = True,
    ) -> str:
        """
        Create a new user in Keycloak.

        Args:
            email: User email
            first_name: First name
            last_name: Last name
            tenant_id: Tenant ID to assign
            enabled: Whether user is enabled

        Returns:
            Created user ID
        """
        token = await self._get_admin_token()

        user_data = {
            "email": email,
            "username": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": enabled,
            "emailVerified": False,
            "attributes": {
                "tenant_id": [tenant_id],
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.admin_url}/users",
                headers={"Authorization": f"Bearer {token}"},
                json=user_data,
            )
            response.raise_for_status()

            # Get user ID from Location header
            location = response.headers.get("Location", "")
            user_id = location.split("/")[-1]

            # Add user to tenant group
            await self._add_user_to_tenant_group(client, token, user_id, tenant_id)

            return user_id

    async def _add_user_to_tenant_group(
        self,
        client: httpx.AsyncClient,
        token: str,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Add user to tenant group."""
        # Get or create tenant group
        group_path = f"/tenants/{tenant_id}"

        # Find group by path
        response = await client.get(
            f"{self.admin_url}/groups",
            headers={"Authorization": f"Bearer {token}"},
            params={"search": tenant_id},
        )

        groups = response.json()
        group_id = None

        for group in groups:
            if group.get("path") == group_path:
                group_id = group["id"]
                break

        if not group_id:
            # Create group
            response = await client.post(
                f"{self.admin_url}/groups",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": tenant_id, "path": group_path},
            )
            if response.status_code == 201:
                location = response.headers.get("Location", "")
                group_id = location.split("/")[-1]

        if group_id:
            # Add user to group
            await client.put(
                f"{self.admin_url}/users/{user_id}/groups/{group_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

    async def delete_user(self, user_id: str) -> None:
        """Delete a user from Keycloak."""
        token = await self._get_admin_token()

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.admin_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

    async def send_verify_email(self, user_id: str) -> None:
        """Send email verification to user."""
        token = await self._get_admin_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.admin_url}/users/{user_id}/send-verify-email",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

    async def send_reset_password_email(self, user_id: str) -> None:
        """Send password reset email to user."""
        token = await self._get_admin_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.admin_url}/users/{user_id}/execute-actions-email",
                headers={"Authorization": f"Bearer {token}"},
                json=["UPDATE_PASSWORD"],
            )
            response.raise_for_status()

    async def update_user_profile(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> None:
        """Update user profile details in Keycloak."""
        token = await self._get_admin_token()

        updates = {}
        if email is not None:
            updates["email"] = email
            updates["username"] = email
        if first_name is not None:
            updates["firstName"] = first_name
        if last_name is not None:
            updates["lastName"] = last_name

        if not updates:
            return

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.admin_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=updates,
            )
            response.raise_for_status()

    async def set_user_password(
        self,
        user_id: str,
        password: str,
        temporary: bool = False,
    ) -> None:
        """Set a user's password in Keycloak."""
        token = await self._get_admin_token()

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.admin_url}/users/{user_id}/reset-password",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "type": "password",
                    "value": password,
                    "temporary": temporary,
                },
            )
            response.raise_for_status()

    async def verify_user_password(self, username: str, password: str) -> bool:
        """Verify user credentials via password grant."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": username,
                    "password": password,
                },
            )
            return response.status_code == 200


# Singleton instance
keycloak_client = KeycloakClient()

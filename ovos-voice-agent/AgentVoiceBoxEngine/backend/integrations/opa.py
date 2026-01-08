"""
OPA (Open Policy Agent) integration client.

Provides policy-based authorization via OPA.
Implements fail-closed security - denies on error.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    """OPA policy decision result."""

    allowed: bool
    reason: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class OPAClient:
    """
    OPA client for policy-based authorization.

    Handles:
    - Policy evaluation
    - Input construction
    - Fail-closed security
    """

    def __init__(self):
        """Initialize OPA client from Django settings."""
        opa_config = getattr(settings, "OPA", {})
        missing = [
            key
            for key in ("URL", "DECISION_PATH", "TIMEOUT_SECONDS", "ENABLED")
            if key not in opa_config
        ]
        if missing:
            raise ValueError(f"OPA configuration missing keys: {', '.join(missing)}")

        self.url = opa_config["URL"]
        self.decision_path = opa_config["DECISION_PATH"]
        self.timeout = opa_config["TIMEOUT_SECONDS"]
        self.enabled = opa_config["ENABLED"]

        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                timeout=self.timeout,
            )
        return self._client

    async def evaluate(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        subject_type: str = "user",
        subject_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Evaluate a policy decision.

        Args:
            action: Action being performed (e.g., "read", "write", "delete")
            resource_type: Type of resource (e.g., "tenant", "project", "session")
            resource_id: ID of the resource (optional)
            subject_type: Type of subject (e.g., "user", "api_key", "system")
            subject_id: ID of the subject
            tenant_id: Tenant context
            context: Additional context for policy evaluation

        Returns:
            PolicyDecision with allowed status and optional reason
        """
        if not self.enabled:
            logger.debug("OPA disabled, allowing request")
            return PolicyDecision(allowed=True, reason="OPA disabled")

        try:
            client = self._get_client()

            # Construct OPA input
            input_data = {
                "input": {
                    "action": action,
                    "resource": {
                        "type": resource_type,
                        "id": resource_id,
                    },
                    "subject": {
                        "type": subject_type,
                        "id": subject_id,
                    },
                    "tenant_id": tenant_id,
                    "context": context or {},
                }
            }

            response = await client.post(
                self.decision_path,
                json=input_data,
            )

            if response.status_code != 200:
                logger.error(
                    f"OPA returned status {response.status_code}: {response.text}"
                )
                # Fail closed
                return PolicyDecision(
                    allowed=False,
                    reason=f"OPA error: status {response.status_code}",
                )

            result = response.json()

            # OPA returns {"result": true/false} or {"result": {"allow": true/false, ...}}
            if isinstance(result.get("result"), bool):
                allowed = result["result"]
                return PolicyDecision(allowed=allowed)
            elif isinstance(result.get("result"), dict):
                allowed = result["result"].get("allow", False)
                reason = result["result"].get("reason")
                details = result["result"].get("details")
                return PolicyDecision(allowed=allowed, reason=reason, details=details)
            else:
                logger.warning(f"Unexpected OPA response format: {result}")
                # Fail closed
                return PolicyDecision(
                    allowed=False,
                    reason="Unexpected OPA response format",
                )

        except httpx.TimeoutException:
            logger.error(f"OPA request timed out after {self.timeout}s")
            # Fail closed
            return PolicyDecision(
                allowed=False,
                reason="OPA timeout",
            )
        except httpx.RequestError as e:
            logger.error(f"OPA request error: {e}")
            # Fail closed
            return PolicyDecision(
                allowed=False,
                reason=f"OPA connection error: {str(e)}",
            )
        except Exception as e:
            logger.exception(f"OPA unexpected error: {e}")
            # Fail closed
            return PolicyDecision(
                allowed=False,
                reason=f"OPA error: {str(e)}",
            )

    async def check_api_access(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        roles: Optional[list] = None,
        api_key_scopes: Optional[list] = None,
    ) -> PolicyDecision:
        """
        Check if an API request is allowed.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            user_id: User ID (if authenticated)
            tenant_id: Tenant ID
            roles: User roles from JWT
            api_key_scopes: API key scopes (if API key auth)

        Returns:
            PolicyDecision
        """
        return await self.evaluate(
            action=method.lower(),
            resource_type="api",
            resource_id=path,
            subject_type="user" if user_id else "anonymous",
            subject_id=user_id,
            tenant_id=tenant_id,
            context={
                "roles": roles or [],
                "api_key_scopes": api_key_scopes or [],
                "path": path,
                "method": method,
            },
        )

    async def check_resource_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        tenant_id: str,
        roles: Optional[list] = None,
    ) -> PolicyDecision:
        """
        Check if a user can perform an action on a resource.

        Args:
            action: Action (read, write, delete, admin)
            resource_type: Resource type
            resource_id: Resource ID
            user_id: User ID
            tenant_id: Tenant ID
            roles: User roles

        Returns:
            PolicyDecision
        """
        return await self.evaluate(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            subject_type="user",
            subject_id=user_id,
            tenant_id=tenant_id,
            context={
                "roles": roles or [],
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
opa_client = OPAClient()

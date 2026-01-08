"""
LLM Configuration and Secret Management Services
================================================

This module provides services for managing Large Language Model (LLM)
configurations and their associated API keys or credentials. It integrates
with HashiCorp Vault to securely store LLM-related secrets on a per-tenant basis,
ensuring that sensitive information is never exposed in the database.
"""

from typing import Optional
from uuid import UUID

from apps.core.exceptions import FeatureNotImplementedError, NotFoundError
from apps.tenants.models import TenantSettings
from integrations.vault import VaultClient


class LLMConfigService:
    """
    A service class responsible for managing LLM configurations and secrets.

    This service acts as an abstraction layer for reading and writing LLM-specific
    credentials and settings, primarily from and to HashiCorp Vault, scoped by tenant.
    """

    # Template for constructing the Vault secret path for tenant-specific LLM secrets.
    SECRET_PATH_TEMPLATE = "agentvoicebox/tenants/{tenant_id}/llm"

    @staticmethod
    def _secret_path(tenant_id: UUID) -> str:
        """
        Generates the Vault secret path for a given tenant's LLM secrets.

        Args:
            tenant_id: The UUID of the tenant.

        Returns:
            A string representing the Vault path.
        """
        return LLMConfigService.SECRET_PATH_TEMPLATE.format(tenant_id=tenant_id)

    @staticmethod
    def get_tenant_settings(tenant_id: UUID) -> TenantSettings:
        """
        Retrieves the `TenantSettings` object for a given tenant.

        This is used to access tenant-specific LLM defaults or other related settings.

        Args:
            tenant_id: The UUID of the tenant.

        Returns:
            The `TenantSettings` instance.

        Raises:
            NotFoundError: If the tenant settings are not found.
        """
        try:
            return TenantSettings.objects.select_related("tenant").get(
                tenant_id=tenant_id
            )
        except TenantSettings.DoesNotExist:
            raise NotFoundError(f"Tenant settings for {tenant_id} not found.")

    @staticmethod
    def read_secrets(tenant_id: UUID) -> dict[str, str]:
        """
        Reads LLM-related secrets (e.g., API keys) from Vault for a specific tenant.

        Args:
            tenant_id: The UUID of the tenant.

        Returns:
            A dictionary containing the secrets, or an empty dictionary if no secrets are found.
        """
        vault = VaultClient()
        vault.initialize()  # Ensure Vault client is authenticated.
        secret = vault.read_secret(LLMConfigService._secret_path(tenant_id))
        return secret.data if secret and secret.data else {}

    @staticmethod
    def write_secrets(tenant_id: UUID, data: dict[str, str]) -> None:
        """
        Writes or updates LLM-related secrets to Vault for a specific tenant.

        Args:
            tenant_id: The UUID of the tenant.
            data: A dictionary of key-value pairs representing the secrets to write.
        """
        vault = VaultClient()
        vault.initialize()  # Ensure Vault client is authenticated.
        ok = vault.write_secret(LLMConfigService._secret_path(tenant_id), data)
        if not ok:
            # Note: FeatureNotImplementedError is a generic APIException.
            # A more specific VaultError might be appropriate in a production system.
            raise FeatureNotImplementedError(
                "Vault write failed", error_code="vault_write_failed"
            )

    @staticmethod
    def merge_secrets(
        existing: dict[str, str], updates: dict[str, Optional[str]]
    ) -> dict[str, str]:
        """
        Merges new secret updates into existing secrets.

        Keys with a `None` value in `updates` will be removed from the merged dictionary.

        Args:
            existing: A dictionary of current secrets.
            updates: A dictionary of secrets to update, where a `None` value indicates deletion.

        Returns:
            A new dictionary with merged secrets.
        """
        merged = dict(existing)
        for key, value in updates.items():
            if value is None:
                if key in merged:
                    del merged[key]  # Remove secret if value is None.
            else:
                merged[key] = value
        return merged

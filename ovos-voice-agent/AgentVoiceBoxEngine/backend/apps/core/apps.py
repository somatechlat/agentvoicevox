"""Core app configuration."""
import logging
import os
import sys

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    """Configuration for the core app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "Core"

    def ready(self):
        """
        Initialize app when Django starts.
        
        Performs fail-fast validation of critical services:
        - HashiCorp Vault connectivity and authentication
        """
        # Skip initialization during migrations or management commands
        if self._is_management_command():
            return

        # Skip if running tests
        if self._is_testing():
            return

        self._initialize_vault()

    def _is_management_command(self) -> bool:
        """Check if running a management command that shouldn't trigger initialization."""
        import sys
        
        # Check for common management commands that shouldn't trigger Vault init
        skip_commands = {
            "migrate",
            "makemigrations",
            "collectstatic",
            "check",
            "shell",
            "dbshell",
            "showmigrations",
            "sqlmigrate",
            "inspectdb",
            "diffsettings",
        }
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command in skip_commands:
                return True
        
        return False

    def _is_testing(self) -> bool:
        """Check if running in test mode."""
        return (
            os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("testing")
            or "pytest" in os.environ.get("_", "")
            or os.environ.get("TESTING", "").lower() == "true"
        )

    def _initialize_vault(self) -> None:
        """
        Initialize Vault client with fail-fast behavior.
        
        If VAULT_FAIL_FAST is True (default), the application will fail to start
        if Vault is unavailable or authentication fails.
        """
        vault_config = getattr(settings, "VAULT", {})
        
        # Skip if Vault is not configured
        if not vault_config.get("ADDR"):
            logger.warning("Vault not configured, skipping initialization")
            return

        try:
            from integrations.vault import vault_client, VaultUnavailableError

            # Initialize the Vault client (performs health check and auth)
            vault_client.initialize()
            logger.info("Vault client initialized successfully")

        except VaultUnavailableError as e:
            # Fail-fast: Vault is required but unavailable
            logger.critical(f"FATAL: Vault unavailable during startup: {e}")
            raise SystemExit(f"Vault unavailable: {e}") from e

        except Exception as e:
            fail_fast = vault_config.get("FAIL_FAST", True)
            
            if fail_fast:
                logger.critical(f"FATAL: Vault initialization failed: {e}")
                raise SystemExit(f"Vault initialization failed: {e}") from e
            else:
                logger.error(f"Vault initialization failed (non-fatal): {e}")

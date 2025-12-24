"""
HashiCorp Vault integration client.

Provides secrets management via Vault.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class VaultSecret:
    """Vault secret representation."""

    data: Dict[str, Any]
    metadata: Dict[str, Any]
    lease_id: Optional[str] = None
    lease_duration: int = 0
    renewable: bool = False


class VaultClient:
    """
    Vault client for secrets management.

    Handles:
    - KV secrets engine v2
    - Dynamic database credentials
    - Transit encryption
    - AppRole authentication
    """

    def __init__(self):
        """Initialize Vault client from Django settings."""
        self.addr = settings.VAULT["ADDR"]
        self.token = settings.VAULT["TOKEN"]
        self.role_id = settings.VAULT["ROLE_ID"]
        self.secret_id = settings.VAULT["SECRET_ID"]
        self.mount_point = settings.VAULT["MOUNT_POINT"]

        self._client = None
        self._token_expires: Optional[datetime] = None

    def _get_client(self):
        """Get or create Vault client."""
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(url=self.addr)

                # Authenticate with token or AppRole
                if self.token:
                    self._client.token = self.token
                elif self.role_id and self.secret_id:
                    self._authenticate_approle()
                else:
                    raise ValueError("Vault token or AppRole credentials required")

                if not self._client.is_authenticated():
                    raise ValueError("Vault authentication failed")

                logger.info(f"Connected to Vault at {self.addr}")

            except ImportError:
                logger.error("hvac package not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Vault: {e}")
                raise

        return self._client

    def _authenticate_approle(self) -> None:
        """Authenticate using AppRole."""
        import hvac

        response = self._client.auth.approle.login(
            role_id=self.role_id,
            secret_id=self.secret_id,
        )

        self._client.token = response["auth"]["client_token"]
        lease_duration = response["auth"]["lease_duration"]
        self._token_expires = datetime.utcnow() + timedelta(seconds=lease_duration - 60)

    def _check_token(self) -> None:
        """Check and refresh token if needed."""
        if self._token_expires and datetime.utcnow() >= self._token_expires:
            logger.info("Vault token expired, re-authenticating")
            self._client = None
            self._get_client()

    # =========================================================================
    # KV Secrets Engine v2
    # =========================================================================

    def read_secret(
        self,
        path: str,
        mount_point: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[VaultSecret]:
        """
        Read a secret from KV v2.

        Args:
            path: Secret path
            mount_point: KV mount point (defaults to configured)
            version: Secret version (defaults to latest)

        Returns:
            VaultSecret or None if not found
        """
        self._check_token()
        client = self._get_client()

        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point or self.mount_point,
                version=version,
            )

            return VaultSecret(
                data=response["data"]["data"],
                metadata=response["data"]["metadata"],
            )

        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            return None

    def write_secret(
        self,
        path: str,
        data: Dict[str, Any],
        mount_point: Optional[str] = None,
    ) -> bool:
        """
        Write a secret to KV v2.

        Args:
            path: Secret path
            data: Secret data
            mount_point: KV mount point

        Returns:
            True if successful
        """
        self._check_token()
        client = self._get_client()

        try:
            client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point or self.mount_point,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write secret {path}: {e}")
            return False

    def delete_secret(
        self,
        path: str,
        mount_point: Optional[str] = None,
    ) -> bool:
        """
        Delete a secret from KV v2.

        Args:
            path: Secret path
            mount_point: KV mount point

        Returns:
            True if successful
        """
        self._check_token()
        client = self._get_client()

        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point or self.mount_point,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            return False

    # =========================================================================
    # Cached Secret Access
    # =========================================================================

    def get_secret(
        self,
        path: str,
        key: Optional[str] = None,
        default: Any = None,
        cache_ttl: int = 300,
    ) -> Any:
        """
        Get a secret with caching.

        Args:
            path: Secret path
            key: Specific key within secret (optional)
            default: Default value if not found
            cache_ttl: Cache TTL in seconds

        Returns:
            Secret value or default
        """
        cache_key = f"vault:{path}"

        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            if key:
                return cached.get(key, default)
            return cached

        # Read from Vault
        secret = self.read_secret(path)
        if secret is None:
            return default

        # Cache the secret
        cache.set(cache_key, secret.data, cache_ttl)

        if key:
            return secret.data.get(key, default)
        return secret.data

    def invalidate_cache(self, path: str) -> None:
        """Invalidate cached secret."""
        cache_key = f"vault:{path}"
        cache.delete(cache_key)

    # =========================================================================
    # Dynamic Database Credentials
    # =========================================================================

    def get_database_credentials(
        self,
        role: str,
        mount_point: str = "database",
    ) -> Optional[Dict[str, str]]:
        """
        Get dynamic database credentials.

        Args:
            role: Database role name
            mount_point: Database secrets engine mount

        Returns:
            Dict with username and password, or None
        """
        self._check_token()
        client = self._get_client()

        try:
            response = client.secrets.database.generate_credentials(
                name=role,
                mount_point=mount_point,
            )

            return {
                "username": response["data"]["username"],
                "password": response["data"]["password"],
                "lease_id": response["lease_id"],
                "lease_duration": response["lease_duration"],
            }

        except Exception as e:
            logger.error(f"Failed to get database credentials for role {role}: {e}")
            return None

    # =========================================================================
    # Transit Encryption
    # =========================================================================

    def encrypt(
        self,
        key_name: str,
        plaintext: str,
        mount_point: str = "transit",
    ) -> Optional[str]:
        """
        Encrypt data using Transit engine.

        Args:
            key_name: Encryption key name
            plaintext: Data to encrypt (base64 encoded)
            mount_point: Transit engine mount

        Returns:
            Ciphertext or None
        """
        self._check_token()
        client = self._get_client()

        try:
            import base64

            # Encode plaintext to base64 if not already
            if not plaintext.startswith("vault:"):
                plaintext = base64.b64encode(plaintext.encode()).decode()

            response = client.secrets.transit.encrypt_data(
                name=key_name,
                plaintext=plaintext,
                mount_point=mount_point,
            )

            return response["data"]["ciphertext"]

        except Exception as e:
            logger.error(f"Failed to encrypt with key {key_name}: {e}")
            return None

    def decrypt(
        self,
        key_name: str,
        ciphertext: str,
        mount_point: str = "transit",
    ) -> Optional[str]:
        """
        Decrypt data using Transit engine.

        Args:
            key_name: Encryption key name
            ciphertext: Data to decrypt
            mount_point: Transit engine mount

        Returns:
            Plaintext or None
        """
        self._check_token()
        client = self._get_client()

        try:
            import base64

            response = client.secrets.transit.decrypt_data(
                name=key_name,
                ciphertext=ciphertext,
                mount_point=mount_point,
            )

            plaintext_b64 = response["data"]["plaintext"]
            return base64.b64decode(plaintext_b64).decode()

        except Exception as e:
            logger.error(f"Failed to decrypt with key {key_name}: {e}")
            return None

    # =========================================================================
    # Health Check
    # =========================================================================

    def is_healthy(self) -> bool:
        """Check if Vault is healthy and accessible."""
        try:
            client = self._get_client()
            health = client.sys.read_health_status(method="GET")
            return health.get("initialized", False) and not health.get("sealed", True)
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False


# Singleton instance
vault_client = VaultClient()

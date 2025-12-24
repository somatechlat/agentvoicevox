"""
HashiCorp Vault integration client.

Provides secrets management via Vault including:
- KV secrets engine v2 for configuration
- Transit engine for encryption/decryption
- Database secrets engine for dynamic credentials
- PKI engine for TLS certificates
- Automatic lease renewal
- Fail-fast startup validation
"""
import base64
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class VaultUnavailableError(Exception):
    """Raised when Vault is unavailable and fail-fast is enabled."""
    pass


class VaultAuthenticationError(Exception):
    """Raised when Vault authentication fails."""
    pass


class VaultEncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


@dataclass
class VaultSecret:
    """Vault secret representation."""
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    lease_id: Optional[str] = None
    lease_duration: int = 0
    renewable: bool = False


@dataclass
class DatabaseCredentials:
    """Dynamic database credentials from Vault."""
    username: str
    password: str
    lease_id: str
    lease_duration: int
    expires_at: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if credentials are expired or about to expire."""
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=buffer_seconds))


@dataclass
class Certificate:
    """TLS certificate from Vault PKI."""
    certificate: str
    private_key: str
    ca_chain: List[str]
    serial_number: str
    expiration: datetime


class VaultClient:
    """
    Vault client for secrets management.

    Handles:
    - KV secrets engine v2
    - Dynamic database credentials with automatic renewal
    - Transit encryption/decryption
    - PKI certificate issuance
    - AppRole authentication with token renewal
    - Fail-fast startup validation
    """

    def __init__(self):
        """Initialize Vault client from Django settings."""
        self.addr = settings.VAULT["ADDR"]
        self.token = settings.VAULT.get("TOKEN")
        self.role_id = settings.VAULT.get("ROLE_ID")
        self.secret_id = settings.VAULT.get("SECRET_ID")
        self.mount_point = settings.VAULT.get("MOUNT_POINT", "secret")
        self.fail_fast = settings.VAULT.get("FAIL_FAST", True)

        self._client = None
        self._token_expires: Optional[datetime] = None
        self._db_credentials: Dict[str, DatabaseCredentials] = {}
        self._renewal_lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize Vault client and validate connectivity.
        
        Raises:
            VaultUnavailableError: If Vault is unavailable and fail_fast is True
            VaultAuthenticationError: If authentication fails
        """
        if self._initialized:
            return

        try:
            client = self._get_client()
            
            if not client.is_authenticated():
                raise VaultAuthenticationError("Vault authentication failed")
            
            # Verify we can access the health endpoint
            health = client.sys.read_health_status(method="GET")
            if health.get("sealed", True):
                raise VaultUnavailableError("Vault is sealed")
            
            self._initialized = True
            logger.info(f"Vault client initialized successfully at {self.addr}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Vault client: {e}"
            logger.error(error_msg)
            
            if self.fail_fast:
                raise VaultUnavailableError(error_msg) from e
            else:
                logger.warning("Vault unavailable but fail_fast is disabled, continuing...")

    def _get_client(self):
        """Get or create Vault client with authentication."""
        if self._client is None:
            try:
                import hvac
                
                self._client = hvac.Client(url=self.addr)

                # Authenticate with token or AppRole
                if self.token:
                    self._client.token = self.token
                    logger.debug("Using token authentication")
                elif self.role_id and self.secret_id:
                    self._authenticate_approle()
                    logger.debug("Using AppRole authentication")
                else:
                    raise VaultAuthenticationError(
                        "Vault token or AppRole credentials required"
                    )

                if not self._client.is_authenticated():
                    raise VaultAuthenticationError("Vault authentication failed")

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
        response = self._client.auth.approle.login(
            role_id=self.role_id,
            secret_id=self.secret_id,
        )

        self._client.token = response["auth"]["client_token"]
        lease_duration = response["auth"]["lease_duration"]
        # Renew 60 seconds before expiration
        self._token_expires = datetime.utcnow() + timedelta(seconds=lease_duration - 60)
        logger.info(f"AppRole authentication successful, token expires in {lease_duration}s")

    def _check_and_renew_token(self) -> None:
        """Check and renew token if needed."""
        if self._token_expires and datetime.utcnow() >= self._token_expires:
            with self._renewal_lock:
                # Double-check after acquiring lock
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
        self._check_and_renew_token()
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
        self._check_and_renew_token()
        client = self._get_client()

        try:
            client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point or self.mount_point,
            )
            logger.debug(f"Secret written to {path}")
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
        self._check_and_renew_token()
        client = self._get_client()

        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point or self.mount_point,
            )
            logger.debug(f"Secret deleted at {path}")
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
    ) -> Optional[DatabaseCredentials]:
        """
        Get dynamic database credentials with automatic renewal.

        Args:
            role: Database role name (backend, temporal-worker, keycloak)
            mount_point: Database secrets engine mount

        Returns:
            DatabaseCredentials or None
        """
        # Check if we have valid cached credentials
        if role in self._db_credentials:
            creds = self._db_credentials[role]
            if not creds.is_expired():
                return creds
            else:
                # Try to renew the lease
                renewed = self._renew_lease(creds.lease_id)
                if renewed:
                    creds.expires_at = datetime.utcnow() + timedelta(seconds=renewed)
                    return creds

        # Generate new credentials
        self._check_and_renew_token()
        client = self._get_client()

        try:
            response = client.secrets.database.generate_credentials(
                name=role,
                mount_point=mount_point,
            )

            creds = DatabaseCredentials(
                username=response["data"]["username"],
                password=response["data"]["password"],
                lease_id=response["lease_id"],
                lease_duration=response["lease_duration"],
                expires_at=datetime.utcnow() + timedelta(
                    seconds=response["lease_duration"]
                ),
            )

            self._db_credentials[role] = creds
            logger.info(
                f"Generated database credentials for role {role}, "
                f"expires in {response['lease_duration']}s"
            )
            return creds

        except Exception as e:
            logger.error(f"Failed to get database credentials for role {role}: {e}")
            return None

    def _renew_lease(self, lease_id: str, increment: int = 3600) -> Optional[int]:
        """
        Renew a Vault lease.

        Args:
            lease_id: Lease ID to renew
            increment: Requested lease duration in seconds

        Returns:
            New lease duration or None if renewal failed
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            response = client.sys.renew_lease(
                lease_id=lease_id,
                increment=increment,
            )
            new_duration = response["lease_duration"]
            logger.debug(f"Renewed lease {lease_id}, new duration: {new_duration}s")
            return new_duration

        except Exception as e:
            logger.warning(f"Failed to renew lease {lease_id}: {e}")
            return None

    def revoke_database_credentials(self, role: str) -> bool:
        """
        Revoke database credentials for a role.

        Args:
            role: Database role name

        Returns:
            True if successful
        """
        if role not in self._db_credentials:
            return True

        creds = self._db_credentials[role]
        self._check_and_renew_token()
        client = self._get_client()

        try:
            client.sys.revoke_lease(lease_id=creds.lease_id)
            del self._db_credentials[role]
            logger.info(f"Revoked database credentials for role {role}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke credentials for role {role}: {e}")
            return False

    # =========================================================================
    # Transit Encryption
    # =========================================================================

    def encrypt(
        self,
        key_name: str,
        plaintext: str,
        mount_point: str = "transit",
        context: Optional[str] = None,
    ) -> str:
        """
        Encrypt data using Transit engine.

        Args:
            key_name: Encryption key name (api-keys, webhook-secrets, tenant-{id})
            plaintext: Data to encrypt
            mount_point: Transit engine mount
            context: Optional context for key derivation

        Returns:
            Ciphertext (vault:v1:... format)

        Raises:
            VaultEncryptionError: If encryption fails
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            # Encode plaintext to base64
            plaintext_b64 = base64.b64encode(plaintext.encode()).decode()

            kwargs = {
                "name": key_name,
                "plaintext": plaintext_b64,
                "mount_point": mount_point,
            }
            if context:
                kwargs["context"] = base64.b64encode(context.encode()).decode()

            response = client.secrets.transit.encrypt_data(**kwargs)
            ciphertext = response["data"]["ciphertext"]
            logger.debug(f"Encrypted data with key {key_name}")
            return ciphertext

        except Exception as e:
            logger.error(f"Failed to encrypt with key {key_name}: {e}")
            raise VaultEncryptionError(f"Encryption failed: {e}") from e

    def decrypt(
        self,
        key_name: str,
        ciphertext: str,
        mount_point: str = "transit",
        context: Optional[str] = None,
    ) -> str:
        """
        Decrypt data using Transit engine.

        Args:
            key_name: Encryption key name
            ciphertext: Data to decrypt (vault:v1:... format)
            mount_point: Transit engine mount
            context: Optional context for key derivation

        Returns:
            Plaintext

        Raises:
            VaultEncryptionError: If decryption fails
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            kwargs = {
                "name": key_name,
                "ciphertext": ciphertext,
                "mount_point": mount_point,
            }
            if context:
                kwargs["context"] = base64.b64encode(context.encode()).decode()

            response = client.secrets.transit.decrypt_data(**kwargs)
            plaintext_b64 = response["data"]["plaintext"]
            plaintext = base64.b64decode(plaintext_b64).decode()
            logger.debug(f"Decrypted data with key {key_name}")
            return plaintext

        except Exception as e:
            logger.error(f"Failed to decrypt with key {key_name}: {e}")
            raise VaultEncryptionError(f"Decryption failed: {e}") from e

    def encrypt_tenant_data(self, tenant_id: str, plaintext: str) -> str:
        """
        Encrypt tenant-specific data.

        Args:
            tenant_id: Tenant UUID
            plaintext: Data to encrypt

        Returns:
            Ciphertext
        """
        return self.encrypt(
            key_name=f"tenant-{tenant_id}",
            plaintext=plaintext,
            context=tenant_id,
        )

    def decrypt_tenant_data(self, tenant_id: str, ciphertext: str) -> str:
        """
        Decrypt tenant-specific data.

        Args:
            tenant_id: Tenant UUID
            ciphertext: Data to decrypt

        Returns:
            Plaintext
        """
        return self.decrypt(
            key_name=f"tenant-{tenant_id}",
            ciphertext=ciphertext,
            context=tenant_id,
        )

    def create_tenant_encryption_key(self, tenant_id: str) -> bool:
        """
        Create a Transit encryption key for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if successful
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            client.secrets.transit.create_key(
                name=f"tenant-{tenant_id}",
                key_type="aes256-gcm96",
                derived=True,  # Enable key derivation for context
                mount_point="transit",
            )
            logger.info(f"Created encryption key for tenant {tenant_id}")
            return True

        except Exception as e:
            # Key might already exist
            if "already exists" in str(e).lower():
                logger.debug(f"Encryption key for tenant {tenant_id} already exists")
                return True
            logger.error(f"Failed to create encryption key for tenant {tenant_id}: {e}")
            return False

    # =========================================================================
    # PKI Engine - TLS Certificates
    # =========================================================================

    def issue_certificate(
        self,
        role: str,
        common_name: str,
        alt_names: Optional[List[str]] = None,
        ip_sans: Optional[List[str]] = None,
        ttl: str = "720h",
        mount_point: str = "pki",
    ) -> Optional[Certificate]:
        """
        Issue a TLS certificate from PKI engine.

        Args:
            role: PKI role name (internal-services, keycloak)
            common_name: Certificate common name
            alt_names: Subject alternative names (DNS)
            ip_sans: IP subject alternative names
            ttl: Certificate TTL
            mount_point: PKI engine mount

        Returns:
            Certificate or None
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            kwargs = {
                "name": role,
                "common_name": common_name,
                "ttl": ttl,
                "mount_point": mount_point,
            }
            if alt_names:
                kwargs["alt_names"] = ",".join(alt_names)
            if ip_sans:
                kwargs["ip_sans"] = ",".join(ip_sans)

            response = client.secrets.pki.generate_certificate(**kwargs)
            data = response["data"]

            # Parse expiration time
            expiration = datetime.utcnow() + timedelta(hours=int(ttl.rstrip("h")))

            cert = Certificate(
                certificate=data["certificate"],
                private_key=data["private_key"],
                ca_chain=data.get("ca_chain", []),
                serial_number=data["serial_number"],
                expiration=expiration,
            )

            logger.info(f"Issued certificate for {common_name}, expires: {expiration}")
            return cert

        except Exception as e:
            logger.error(f"Failed to issue certificate for {common_name}: {e}")
            return None

    def get_ca_certificate(self, mount_point: str = "pki") -> Optional[str]:
        """
        Get the CA certificate in PEM format.

        Args:
            mount_point: PKI engine mount

        Returns:
            CA certificate PEM or None
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            response = client.secrets.pki.read_ca_certificate(mount_point=mount_point)
            return response

        except Exception as e:
            logger.error(f"Failed to get CA certificate: {e}")
            return None

    def get_ca_chain(self, mount_point: str = "pki") -> Optional[str]:
        """
        Get the CA certificate chain in PEM format.

        Args:
            mount_point: PKI engine mount

        Returns:
            CA chain PEM or None
        """
        self._check_and_renew_token()
        client = self._get_client()

        try:
            response = client.secrets.pki.read_ca_certificate_chain(
                mount_point=mount_point
            )
            return response

        except Exception as e:
            logger.error(f"Failed to get CA chain: {e}")
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

    def get_health_details(self) -> Dict[str, Any]:
        """Get detailed health information."""
        try:
            client = self._get_client()
            health = client.sys.read_health_status(method="GET")
            return {
                "healthy": health.get("initialized", False) and not health.get("sealed", True),
                "initialized": health.get("initialized", False),
                "sealed": health.get("sealed", True),
                "version": health.get("version", "unknown"),
                "cluster_name": health.get("cluster_name", "unknown"),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


# Singleton instance
vault_client = VaultClient()


def get_vault_client() -> VaultClient:
    """Get the Vault client singleton."""
    return vault_client

"""
Django settings loader.

Automatically loads the appropriate settings module based on DJANGO_SETTINGS_MODULE.
Validates required environment variables on import.
"""
import os

from pydantic import ValidationError

from .env_config import Settings

# Load and validate environment configuration
try:
    settings_config = Settings()
except ValidationError as e:
    import sys
    print("=" * 60, file=sys.stderr)
    print("CONFIGURATION ERROR: Missing or invalid environment variables", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for error in e.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        print(f"  - {field}: {error['msg']}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)

# Export settings config for use in settings modules
__all__ = ["settings_config"]

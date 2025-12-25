"""
Django settings loader.

Automatically loads the appropriate settings module based on DJANGO_SETTINGS_MODULE.
Validates required environment variables on import.

All configuration is centralized through Django's settings framework.
Environment variables are validated at startup using pydantic-settings.
"""
import os
import sys

# Note: settings_config module is imported directly by base.py
# This file just ensures the package is properly initialized

"""
WSGI config for AgentVoiceBox Platform.

This is used for traditional synchronous deployments.
For production, use ASGI (config/asgi.py) with Uvicorn.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_wsgi_application()

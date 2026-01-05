"""
ASGI config for AgentVoiceBox Platform.

Configures the ASGI application with:
- HTTP routing to Django
- WebSocket routing to Django Channels consumers

WebSocket routes:
- /ws/v2/events              - Event streaming
- /ws/v2/sessions/{id}       - Voice session communication
- /ws/v2/stt/transcription   - STT streaming
- /ws/v2/tts/stream          - TTS streaming
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Initialize Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
from realtime.middleware import WebSocketAuthMiddleware  # noqa: E402
from realtime.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        # HTTP requests -> Django
        "http": django_asgi_app,
        # WebSocket requests -> Django Channels
        "websocket": AllowedHostsOriginValidator(
            WebSocketAuthMiddleware(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)))
        ),
    }
)

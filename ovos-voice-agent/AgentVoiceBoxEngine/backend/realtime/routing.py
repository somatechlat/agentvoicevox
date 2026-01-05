"""
WebSocket URL routing for Django Channels.
"""

from django.urls import path, re_path

from .consumers import EventConsumer, SessionConsumer, STTConsumer, TTSConsumer

websocket_urlpatterns = [
    # Event streaming
    path("ws/v2/events", EventConsumer.as_asgi()),
    # Voice session
    re_path(r"ws/v2/sessions/(?P<session_id>[0-9a-f-]+)$", SessionConsumer.as_asgi()),
    # STT streaming
    path("ws/v2/stt/transcription", STTConsumer.as_asgi()),
    # TTS streaming
    path("ws/v2/tts/stream", TTSConsumer.as_asgi()),
]

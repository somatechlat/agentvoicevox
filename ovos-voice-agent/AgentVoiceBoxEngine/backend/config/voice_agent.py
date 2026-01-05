"""
Voice agent configuration accessors.
"""

from django.conf import settings


def voice_agent_base_url() -> str:
    """Return the public HTTP base URL for the voice agent."""
    return settings.VOICE_AGENT["BASE_URL"]


def voice_agent_ws_base_url() -> str:
    """Return the public WebSocket base URL for the voice agent."""
    return settings.VOICE_AGENT["WS_BASE_URL"]

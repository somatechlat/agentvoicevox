"""
Voice session WebSocket consumer.

Handles real-time voice communication for sessions.
"""
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class SessionConsumer(BaseConsumer):
    """
    Voice session consumer.

    Handles:
    - Audio streaming (input/output)
    - Transcription results
    - LLM responses
    - Session events
    """

    def __init__(self, *args, **kwargs):
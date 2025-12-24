"""
STT (Speech-to-Text) streaming WebSocket consumer.
"""
import logging
from typing import Any, Dict

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class STTConsumer(BaseConsumer):
    """
    STT streaming consumer.

    Handles real-time speech-to-text transcription.
    """

    async def connect(self):
        """Handle connection."""
        await super().connect()

        if se
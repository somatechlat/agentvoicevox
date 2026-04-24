"""
OVOS Intelligence Bridge.
Connects AgentVoiceBox realtime sessions to the OpenVoiceOS (OVOS) Message Bus.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from ovos_bus_client import Message, MessageBusClient

from config.settings import settings_config as env

logger = logging.getLogger(__name__)


class OVOSIntelligenceBridge:
    _instance: Optional['OVOSIntelligenceBridge'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OVOSIntelligenceBridge, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.host = env.ovos_bus_host
        self.port = env.ovos_bus_port
        self.client = MessageBusClient(host=self.host, port=self.port)
        self._loop = asyncio.get_event_loop()
        self._session_callbacks: Dict[str, Callable] = {}
        self._initialized = True

    async def connect(self):
        """ESTABLISH connection to the OVOS message bus."""
        logger.info(f"Connecting to OVOS bus at {self.host}:{self.port}...")
        try:
            # MessageBusClient.run_in_thread() is common, but we want async integration
            self.client.run_in_thread()
            self.client.on("speak", self._handle_speak)
            logger.info("Connected to OVOS bus.")
        except Exception as e:
            logger.error(f"Failed to connect to OVOS bus: {str(e)}")
            raise

    def register_session(self, session_id: str, callback: Callable[[str, Dict[str, Any]], Any]):
        """Registers a callback for 'speak' events belonging to a specific session."""
        self._session_callbacks[session_id] = callback

    def unregister_session(self, session_id: str):
        """Unregisters a session callback."""
        if session_id in self._session_callbacks:
            del self._session_callbacks[session_id]

    async def send_utterance(self, session_id: str, text: str, context: Optional[Dict[str, Any]] = None):
        """
        Sends an utterance to the OVOS bus for intent processing.
        """
        context = context or {}
        context["session_id"] = session_id

        message = Message(
            "recognizer_loop:utterance",
            data={"utterances": [text]},
            context=context
        )
        logger.debug(f"Forwarding utterance to OVOS: {text} [Session: {session_id}]")
        self.client.emit(message)

    def _handle_speak(self, message: Message):
        """
        Internal handler for OVOS 'speak' messages.
        Dispatches to the registered session callback.
        """
        utterance = message.data.get("utterance")
        session_id = message.context.get("session_id")

        if not utterance or not session_id:
            return

        callback = self._session_callbacks.get(session_id)
        if callback:
            logger.debug(f"OVOS speaking: {utterance} [Session: {session_id}]")
            # Callback is likely a coroutine or a sync function that triggers Redis/WS
            if asyncio.iscoroutinefunction(callback):
                asyncio.run_coroutine_threadsafe(callback(utterance, message.context), self._loop)
            else:
                self._loop.call_soon_threadsafe(callback, utterance, message.context)

    async def disconnect(self):
        """Cleanly closes the OVOS bus connection."""
        self.client.close()
        logger.info("Disconnected from OVOS bus.")

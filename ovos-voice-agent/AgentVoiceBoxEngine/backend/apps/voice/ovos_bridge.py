"""
OVOS Configuration Bridge
=========================

This module bridges the Django-based voice configurations (Personas and Models)
with the OVOS message bus. When a Persona is updated via the API, or when a session
starts, this bridge ensures OVOS is aware of the desired configuration (e.g., TTS voice,
STT language, LLM system prompt).
"""

import json
import logging
from typing import Any, Dict

from ovos_bus_client import Message, MessageBusClient
from ovos_utils.log import LOG

logger = logging.getLogger(__name__)

class OVOSConfigBridge:
    """
    Manages pushing configuration state from Django models to the OVOS message bus.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OVOSConfigBridge, cls).__new__(cls)
            cls._instance.client = MessageBusClient()
            cls._instance.connected = False
        return cls._instance
        
    def connect(self):
        """Connects to the OVOS message bus."""
        if not self.connected:
            try:
                self.client.run_in_thread()
                self.connected = True
                logger.info("OVOSConfigBridge connected to ovos-bus.")
            except Exception as e:
                logger.error(f"Failed to connect to ovos-bus: {e}")
                
    def disconnect(self):
        """Disconnects from the OVOS message bus."""
        if self.connected:
            self.client.close()
            self.connected = False

    def emit_configuration_patch(self, config_patch: Dict[str, Any]):
        """
        Emits a configuration.patch message to update OVOS core settings.
        
        Args:
            config_patch: A dictionary containing the configuration keys to update.
        """
        if not self.connected:
            self.connect()
            
        message = Message("configuration.patch", data={"config": config_patch})
        self.client.emit(message)
        logger.info(f"Emitted configuration.patch to OVOS bus: {config_patch}")

    def apply_persona_to_session(self, session_id: str, persona_config: Dict[str, Any]):
        """
        Applies a VoicePersona configuration to a specific session context.
        This prepares the session data in OVOS so that subsequent utterances
        on this session use these settings (TTS voice, language, etc).
        
        Args:
            session_id: The unique ID of the voice session.
            persona_config: The dictionary from VoicePersona.to_config().
        """
        if not self.connected:
            self.connect()
            
        # Example: we might inject session-specific config via the bus.
        # OVOS allows passing context for plugins.
        context_update = {
            "session_id": session_id,
            "tts": {
                "module": "ovos-tts-plugin-kokoro" if "kokoro" in persona_config["voice"]["id"] else "default",
                "voice": persona_config["voice"]["id"]
            },
            "lang": persona_config["stt"]["language"],
            "llm": {
                "model": persona_config["llm"]["model"],
                "system_prompt": persona_config["llm"]["system_prompt"],
                "temperature": persona_config["llm"]["temperature"],
            }
        }
        
        # We can either emit a custom event to notify session creation
        # or rely on attaching this context to the first audio frame.
        message = Message("avb.session.configured", data={}, context=context_update)
        self.client.emit(message)
        logger.info(f"Emitted session configuration for {session_id}")

    def get_active_configuration(self) -> Dict[str, Any]:
        """
        Synchronously requests the active configuration from the OVOS bus.
        
        Returns:
            A dictionary containing the active mycroft.conf settings, or empty dict if timeout.
        """
        if not self.connected:
            self.connect()
            
        request_msg = Message("configuration.request")
        response = self.client.wait_for_response(request_msg, timeout=3.0)
        
        if response and response.data:
            return response.data.get("config", {})
            
        logger.warning("OVOS configuration.request timed out or returned no data.")
        return {}
        
    def get_available_plugins(self) -> Dict[str, Any]:
        """
        Queries the OVOS bus for available TTS and STT plugins.
        This provides a dynamic list of installed capabilities.
        
        Returns:
            Dictionary with installed plugins, e.g. {"tts": [], "stt": []}
        """
        if not self.connected:
            self.connect()
            
        # Try to query TTS plugins
        tts_req = Message("opm.tts.query")
        tts_resp = self.client.wait_for_response(tts_req, timeout=2.0)
        
        # Try to query STT plugins
        stt_req = Message("opm.stt.query")
        stt_resp = self.client.wait_for_response(stt_req, timeout=2.0)
        
        # Fallback to configuration if plugins not responding (Vibe Coding Rule 1)
        fallback_config = self.get_active_configuration()
        
        plugins = {
            "tts": tts_resp.data.get("plugins", []) if tts_resp else [],
            "stt": stt_resp.data.get("plugins", []) if stt_resp else []
        }
        
        if not plugins["tts"] and "tts" in fallback_config:
            plugins["tts"] = [fallback_config["tts"].get("module", "default")]
            
        if not plugins["stt"] and "stt" in fallback_config:
            plugins["stt"] = [fallback_config["stt"].get("module", "default")]
            
        return plugins

# Global singleton instance
ovos_config_bridge = OVOSConfigBridge()

"""
MCP Core Tools
==============
Defines the core tool implementations exposed via the Model Context Protocol.

These functions wrap existing service layer logic (e.g., VoiceModelService, TTSActivities)
to provide a simplified, type-safe interface for MCP clients. They handle:
- Input validation
- Context extraction (tenant/session)
- Service layer orchestration
- Data serialization (e.g., base64 encoding audio)
"""

import base64

import logging
from uuid import uuid4

from mcp.server.fastmcp import Context

from apps.voice.services import VoiceModelService
from apps.workflows.activities.tts import TTSActivities, SynthesisRequest

logger = logging.getLogger(__name__)

from asgiref.sync import sync_to_async

async def list_voices() -> list[dict]:
    """
    Lists all available text-to-speech voices provided by the platform.
    """
    # Wrap blocking DB call
    models, _ = await sync_to_async(VoiceModelService.list_models)(active_only=True)
    
    # Since models is a QuerySet/List of ORM objects, accessing fields might lazily trigger DB
    # But list_models returns a list, so data is already fetched.
    return [
        {
            "id": m.id,
            "name": m.name,
            "provider": m.provider,
            "language": m.language,
            "gender": m.gender,
        }
        for m in models
    ]

async def generate_speech(
    text: str,
    voice_id: str = "af_heart",
    speed: float = 1.0,
    ctx: Context = None,
) -> str:
    """
    Synthesizes speech from text using the specified voice.
    
    Args:
        text: The text to convert to speech.
        voice_id: The ID of the voice to use (default: 'af_heart').
        speed: Speaking speed multiplier (default: 1.0).
        
    Returns:
        Base64 encoded audio data (WAV format).
    """
    # For now, we use a temporary/system tenant ID since we are running via stdio
    # In a real scenario, we would extract this from the MCP authentication context
    tenant_id = "mcp-system-user"
    session_id = f"mcp-{uuid4()}"

    request = SynthesisRequest(
        tenant_id=tenant_id,
        session_id=session_id,
        text=text,
        voice_id=voice_id,
        speed=speed,
        output_format="wav",
    )

    # Instantiate activities directly (since they don't depend on Temporal context for this method)
    activities = TTSActivities()
    
    try:
        result = await activities.synthesize_speech(request)
        
        # Encode audio bytes to base64 string for safe transport
        audio_b64 = base64.b64encode(result.audio_data).decode("utf-8")
        
        logger.info(f"Generated speech for '{text[:20]}...' using {voice_id}")
        return audio_b64
    except Exception as e:
        logger.error(f"Failed to generate speech: {e}")
        raise

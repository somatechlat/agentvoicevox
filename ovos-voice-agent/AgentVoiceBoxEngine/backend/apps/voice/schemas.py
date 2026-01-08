"""
Pydantic Schemas for Voice API
=================================

This module defines the Pydantic schemas used for data validation and serialization
in the voice configuration API. These schemas define the public contract of the API,
ensuring that request payloads are valid and that responses have a consistent
structure.

The schemas are organized by resource:
- Voice Persona Schemas: For creating, updating, and viewing voice personas.
- Voice Model Schemas: For viewing and managing system-wide TTS voice models.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema


# ==========================================================================
# VOICE PERSONA SCHEMAS
# ==========================================================================
class VoicePersonaCreate(Schema):
    """
    Defines the request payload for creating a new voice persona.
    All fields have sensible defaults to allow for quick setup.
    """

    name: str  # The human-readable name for the persona.
    description: str = ""  # Optional description of the persona's character.
    voice_id: str = "af_heart"  # The ID of the TTS voice model to use.
    voice_speed: float = 1.0  # Speech speed multiplier (1.0 = normal).
    stt_model: str = "tiny"  # The Whisper model for Speech-to-Text.
    stt_language: str = "en"  # The language code for STT.
    llm_provider: str = (
        "groq"  # The provider for the Large Language Model (e.g., 'groq', 'openai').
    )
    llm_model: str = "llama-3.3-70b-versatile"  # The specific LLM to use.
    system_prompt: str = ""  # The system prompt that defines the LLM's personality.
    temperature: float = 0.7  # LLM creativity control (0.0 to 1.0).
    max_tokens: int = 1024  # Maximum tokens for the LLM response.
    solvers: list[str] = []  # A list of enabled 'solver' plugins for tool use.
    turn_detection_enabled: bool = (
        True  # Whether to automatically detect when the user has finished speaking.
    )
    turn_detection_threshold: float = 0.5  # Confidence threshold for turn detection.
    silence_duration_ms: int = 500  # Silence duration (ms) to trigger end of turn.
    is_default: bool = (
        False  # If true, this persona will be the default for the tenant.
    )


class VoicePersonaUpdate(Schema):
    """
    Defines the request payload for updating an existing voice persona.
    All fields are optional, allowing for partial updates (PATCH).
    """

    name: Optional[str] = None  # The human-readable name for the persona.
    description: Optional[str] = (
        None  # Optional description of the persona's character.
    )
    voice_id: Optional[str] = None  # The ID of the TTS voice model to use.
    voice_speed: Optional[float] = None  # Speech speed multiplier (1.0 = normal).
    stt_model: Optional[str] = None  # The Whisper model for Speech-to-Text.
    stt_language: Optional[str] = None  # The language code for STT.
    llm_provider: Optional[str] = None  # The provider for the Large Language Model.
    llm_model: Optional[str] = None  # The specific LLM to use.
    system_prompt: Optional[str] = (
        None  # The system prompt that defines the LLM's personality.
    )
    temperature: Optional[float] = None  # LLM creativity control (0.0 to 1.0).
    max_tokens: Optional[int] = None  # Maximum tokens for the LLM response.
    solvers: Optional[list[str]] = None  # A list of enabled 'solver' plugins.
    turn_detection_enabled: Optional[bool] = (
        None  # Enable/disable automatic turn detection.
    )
    turn_detection_threshold: Optional[float] = (
        None  # Confidence threshold for turn detection.
    )
    silence_duration_ms: Optional[int] = (
        None  # Silence duration (ms) to trigger end of turn.
    )
    is_active: Optional[bool] = None  # Set the persona to active or inactive.
    is_default: Optional[bool] = None  # Set the persona as the tenant's default.


class VoicePersonaOut(Schema):
    """
    Defines the response structure for a single voice persona object.
    This schema is used for GET, POST, and PATCH responses.
    """

    id: UUID  # The unique identifier for the voice persona.
    tenant_id: UUID  # The ID of the tenant that owns this persona.
    name: str
    description: str
    voice_id: str
    voice_speed: float
    stt_model: str
    stt_language: str
    llm_provider: str
    llm_model: str
    system_prompt: str
    temperature: float
    max_tokens: int
    solvers: list[str]
    usage_count: int  # Number of times this persona has been used.
    turn_detection_enabled: bool
    turn_detection_threshold: float
    silence_duration_ms: int
    is_active: bool  # Whether the persona is currently active.
    is_default: bool  # Whether this is the default persona for the tenant.
    created_at: datetime  # Timestamp of when the persona was created.
    updated_at: datetime  # Timestamp of the last update.


class VoicePersonaConfigOut(Schema):
    """
    Defines the response for a persona's session configuration.
    This is a structured, nested dictionary used by client applications to
    configure a voice session.
    """

    voice: dict[str, Any]  # Contains 'id' and 'speed' for TTS.
    stt: dict[str, Any]  # Contains 'model' and 'language' for STT.
    llm: dict[str, Any]  # Contains LLM parameters like 'provider', 'model', etc.
    turn_detection: dict[str, Any]  # Contains VAD parameters.


class VoicePersonaListOut(Schema):
    """
    Defines the response structure for a paginated list of voice personas.
    """

    items: list[VoicePersonaOut]  # The list of personas on the current page.
    total: int  # The total number of personas matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.


class VoicePersonaTestRequest(Schema):
    """
    Defines the request payload for testing a voice persona's LLM.
    """

    message: str  # The user message to send to the LLM.


class VoicePersonaTestResponse(Schema):
    """
    Defines the response structure for a voice persona LLM test.
    """

    response: str  # The text response generated by the LLM.


# ==========================================================================
# VOICE MODEL SCHEMAS
# ==========================================================================
class VoiceModelCreate(Schema):
    """
    Defines the request payload for creating a new system-wide voice model.
    This is an admin-only operation.
    """

    id: str  # The unique ID for the model (e.g., 'provider-VoiceName').
    name: str  # The human-readable name of the voice.
    provider: str  # The provider of the voice model (e.g., 'kokoro').
    language: str = "en"  # The language code of the voice.
    gender: str = ""  # The perceived gender of the voice.
    description: str = ""  # A short description of the voice's character.
    sample_url: str = ""  # A URL to an audio sample.
    is_active: bool = True  # Whether the model is available for use.


class VoiceModelUpdate(Schema):
    """
    Defines the request payload for updating an existing voice model.
    All fields are optional for partial updates. Admin-only operation.
    """

    name: Optional[str] = None
    provider: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    sample_url: Optional[str] = None
    is_active: Optional[bool] = None


class VoiceModelOut(Schema):
    """
    Defines the response structure for a single voice model object.
    """

    id: str
    name: str
    provider: str
    language: str
    gender: str
    description: str
    sample_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VoiceModelListOut(Schema):
    """
    Defines the response structure for a list of voice models.
    """

    items: list[VoiceModelOut]  # The list of voice models.
    total: int  # The total number of models returned.


class VoiceProvidersOut(Schema):
    """

    Defines the response structure for the list of available voice providers.
    """

    providers: list[
        str
    ]  # A list of unique provider names (e.g., ['kokoro', 'phoonnx']).


class VoiceLanguagesOut(Schema):
    """
    Defines the response structure for the list of available voice languages.
    """

    languages: list[str]  # A list of unique language codes (e.g., ['en', 'es', 'fr']).

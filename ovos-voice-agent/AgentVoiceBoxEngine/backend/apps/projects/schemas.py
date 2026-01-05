"""
Pydantic Schemas for the Project API
=====================================

This module defines the Pydantic schemas for data validation and serialization
in the Project API endpoints. It includes detailed schemas for the various
sub-configurations of a project, such as STT, TTS, and LLM settings.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema


# ==========================================================================
# Reusable Configuration Component Schemas
# ==========================================================================
class STTConfig(Schema):
    """Defines the structure for Speech-to-Text (STT) configuration."""
    model: str = "tiny"  # The Whisper model size to use for transcription.
    language: str = "en"  # The language code for STT processing (e.g., 'en', 'es').


class TTSConfig(Schema):
    """Defines the structure for Text-to-Speech (TTS) configuration."""
    model: str = "kokoro"  # The TTS provider/model to use.
    voice: str = "af_heart"  # The specific voice ID for speech synthesis.
    speed: float = 1.0  # Speech speed multiplier (1.0 is normal).


class LLMConfig(Schema):
    """Defines the structure for Large Language Model (LLM) configuration."""
    provider: str = "groq"  # The LLM provider (e.g., 'groq', 'openai').
    model: str = "llama-3.3-70b-versatile"  # The specific LLM for generating responses.
    temperature: float = 0.7  # Creativity control (higher is more creative).
    max_tokens: int = 1024  # The maximum number of tokens for a response.


class TurnDetectionConfig(Schema):
    """Defines the structure for Voice Activity Detection (VAD) / turn detection."""
    enabled: bool = True  # If true, automatically detect when a user has finished speaking.
    threshold: float = 0.5  # Confidence threshold for detecting speech.
    prefix_padding: float = 0.3  # Audio padding (in seconds) to include before speech starts.
    silence_duration: float = 0.5  # Duration of silence (in seconds) to consider a turn complete.


class VoiceConfig(Schema):
    """A composite schema representing the full, structured voice agent configuration."""
    stt: Optional[STTConfig] = None
    tts: Optional[TTSConfig] = None
    llm: Optional[LLMConfig] = None
    turn_detection: Optional[TurnDetectionConfig] = None
    system_prompt: Optional[str] = None  # The base instruction prompt for the agent.


# ==========================================================================
# Main Project Schemas
# ==========================================================================
class ProjectBase(Schema):
    """A base schema with the core identifying fields of a project."""
    name: str  # The human-readable name of the project.
    slug: str  # A URL-friendly identifier, unique within the tenant.
    description: str = ""  # An optional description of the project's purpose.


class ProjectCreate(ProjectBase):
    """
    Defines the request payload for creating a new project.

    This schema has a flat structure with default values for all configuration
    settings, allowing for quick project creation with minimal input.
    """
    stt_model: str = "tiny"
    stt_language: str = "en"
    tts_model: str = "kokoro"
    tts_voice: str = "af_heart"
    tts_speed: float = 1.0
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    system_prompt: str = ""
    turn_detection_enabled: bool = True
    max_session_duration: int = 3600  # Max session time in seconds (default 1 hour).
    max_concurrent_sessions: int = 10  # Max concurrent sessions for this project.


class ProjectUpdate(Schema):
    """
    Defines the request payload for updating a project.
    All fields are optional to allow for partial (PATCH) updates.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    # Voice agent settings
    stt_model: Optional[str] = None
    stt_language: Optional[str] = None
    tts_model: Optional[str] = None
    tts_voice: Optional[str] = None
    tts_speed: Optional[float] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None

    # Turn detection settings
    turn_detection_enabled: Optional[bool] = None
    turn_detection_threshold: Optional[float] = None
    turn_detection_prefix_padding: Optional[float] = None
    turn_detection_silence_duration: Optional[float] = None

    # Session and webhook settings
    max_session_duration: Optional[int] = None
    max_concurrent_sessions: Optional[int] = None
    webhook_url: Optional[str] = None
    webhook_events: Optional[list[str]] = None

    # Miscellaneous settings
    settings: Optional[dict[str, Any]] = None


class ProjectResponse(Schema):
    """
    Defines the standard response structure for a single project object.
    This schema presents a flat view of all project configurations.
    """
    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: str
    is_active: bool

    # Voice agent config
    stt_model: str
    stt_language: str
    tts_model: str
    tts_voice: str
    tts_speed: float
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    system_prompt: str

    # Turn detection config
    turn_detection_enabled: bool
    turn_detection_threshold: float
    turn_detection_prefix_padding: float
    turn_detection_silence_duration: float

    # Limits and webhooks
    max_session_duration: int
    max_concurrent_sessions: int
    webhook_url: str
    webhook_events: list[str]

    # Metadata
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_orm(project) -> "ProjectResponse":
        """
        Creates a `ProjectResponse` instance from a Django `Project` model instance.

        Args:
            project: The Django `Project` model instance.

        Returns:
            An instance of `ProjectResponse`.
        """
        return ProjectResponse(
            id=project.id,
            tenant_id=project.tenant_id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            is_active=project.is_active,
            stt_model=project.stt_model,
            stt_language=project.stt_language,
            tts_model=project.tts_model,
            tts_voice=project.tts_voice,
            tts_speed=project.tts_speed,
            llm_provider=project.llm_provider,
            llm_model=project.llm_model,
            llm_temperature=project.llm_temperature,
            llm_max_tokens=project.llm_max_tokens,
            system_prompt=project.system_prompt,
            turn_detection_enabled=project.turn_detection_enabled,
            turn_detection_threshold=project.turn_detection_threshold,
            turn_detection_prefix_padding=project.turn_detection_prefix_padding,
            turn_detection_silence_duration=project.turn_detection_silence_duration,
            max_session_duration=project.max_session_duration,
            max_concurrent_sessions=project.max_concurrent_sessions,
            webhook_url=project.webhook_url or "",
            webhook_events=project.webhook_events or [],
            created_by_id=project.created_by_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class ProjectListResponse(Schema):
    """
    Defines the response structure for a paginated list of projects.
    """
    items: list[ProjectResponse]  # The list of projects on the current page.
    total: int  # The total number of projects matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.
    pages: int  # The total number of pages.


class ProjectVoiceConfigResponse(Schema):
    """
    Defines a structured response for a project's voice configuration.

    This schema composes the smaller config components into a nested structure,
    which is ideal for client applications to consume.
    """
    project_id: UUID
    stt: STTConfig
    tts: TTSConfig
    llm: LLMConfig
    turn_detection: TurnDetectionConfig
    system_prompt: str

    @staticmethod
    def from_project(project) -> "ProjectVoiceConfigResponse":
        """
        Creates a structured `ProjectVoiceConfigResponse` from a `Project` model.

        Args:
            project: The Django `Project` model instance.

        Returns:
            An instance of `ProjectVoiceConfigResponse`.
        """
        return ProjectVoiceConfigResponse(
            project_id=project.id,
            stt=STTConfig(model=project.stt_model, language=project.stt_language),
            tts=TTSConfig(
                model=project.tts_model,
                voice=project.tts_voice,
                speed=project.tts_speed,
            ),
            llm=LLMConfig(
                provider=project.llm_provider,
                model=project.llm_model,
                temperature=project.llm_temperature,
                max_tokens=project.llm_max_tokens,
            ),
            turn_detection=TurnDetectionConfig(
                enabled=project.turn_detection_enabled,
                threshold=project.turn_detection_threshold,
                prefix_padding=project.turn_detection_prefix_padding,
                silence_duration=project.turn_detection_silence_duration,
            ),
            system_prompt=project.system_prompt,
        )


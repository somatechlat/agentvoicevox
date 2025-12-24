"""
Pydantic schemas for Project API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema


class STTConfig(Schema):
    """STT configuration schema."""
    model: str = "tiny"
    language: str = "en"


class TTSConfig(Schema):
    """TTS configuration schema."""
    model: str = "kokoro"
    voice: str = "af_heart"
    speed: float = 1.0


class LLMConfig(Schema):
    """LLM configuration schema."""
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 1024


class TurnDetectionConfig(Schema):
    """Turn detection configuration schema."""
    enabled: bool = True
    threshold: float = 0.5
    prefix_padding: float = 0.3
    silence_duration: float = 0.5


class VoiceConfig(Schema):
    """Complete voice configuration schema."""
    stt: Optional[STTConfig] = None
    tts: Optional[TTSConfig] = None
    llm: Optional[LLMConfig] = None
    turn_detection: Optional[TurnDetectionConfig] = None
    system_prompt: Optional[str] = None


class ProjectBase(Schema):
    """Base project schema."""
    name: str
    slug: str
    description: str = ""


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
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
    max_session_duration: int = 3600
    max_concurrent_sessions: int = 10


class ProjectUpdate(Schema):
    """Schema for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
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
    turn_detection_enabled: Optional[bool] = None
    turn_detection_threshold: Optional[float] = None
    turn_detection_prefix_padding: Optional[float] = None
    turn_detection_silence_duration: Optional[float] = None
    max_session_duration: Optional[int] = None
    max_concurrent_sessions: Optional[int] = None
    webhook_url: Optional[str] = None
    webhook_events: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(Schema):
    """Schema for project response."""
    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: str
    is_active: bool
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
    turn_detection_enabled: bool
    turn_detection_threshold: float
    turn_detection_prefix_padding: float
    turn_detection_silence_duration: float
    max_session_duration: int
    max_concurrent_sessions: int
    webhook_url: str
    webhook_events: List[str]
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_orm(project) -> "ProjectResponse":
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
    """Schema for paginated project list."""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProjectVoiceConfigResponse(Schema):
    """Schema for project voice configuration."""
    project_id: UUID
    stt: STTConfig
    tts: TTSConfig
    llm: LLMConfig
    turn_detection: TurnDetectionConfig
    system_prompt: str

    @staticmethod
    def from_project(project) -> "ProjectVoiceConfigResponse":
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

"""
Pydantic schemas for voice configuration API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema


# ==========================================================================
# VOICE PERSONA SCHEMAS
# ==========================================================================
class VoicePersonaCreate(Schema):
    """Schema for creating a voice persona."""

    name: str
    description: str = ""
    voice_id: str = "af_heart"
    voice_speed: float = 1.0
    stt_model: str = "tiny"
    stt_language: str = "en"
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    turn_detection_enabled: bool = True
    turn_detection_threshold: float = 0.5
    silence_duration_ms: int = 500
    is_default: bool = False


class VoicePersonaUpdate(Schema):
    """Schema for updating a voice persona."""

    name: Optional[str] = None
    description: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = None
    stt_model: Optional[str] = None
    stt_language: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    turn_detection_enabled: Optional[bool] = None
    turn_detection_threshold: Optional[float] = None
    silence_duration_ms: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class VoicePersonaOut(Schema):
    """Schema for voice persona response."""

    id: UUID
    tenant_id: UUID
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
    turn_detection_enabled: bool
    turn_detection_threshold: float
    silence_duration_ms: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class VoicePersonaConfigOut(Schema):
    """Schema for voice persona configuration (for sessions)."""

    voice: Dict[str, Any]
    stt: Dict[str, Any]
    llm: Dict[str, Any]
    turn_detection: Dict[str, Any]


class VoicePersonaListOut(Schema):
    """Schema for paginated voice persona list."""

    items: List[VoicePersonaOut]
    total: int
    page: int
    page_size: int


# ==========================================================================
# VOICE MODEL SCHEMAS
# ==========================================================================
class VoiceModelCreate(Schema):
    """Schema for creating a voice model."""

    id: str
    name: str
    provider: str
    language: str = "en"
    gender: str = ""
    description: str = ""
    sample_url: str = ""
    is_active: bool = True


class VoiceModelUpdate(Schema):
    """Schema for updating a voice model."""

    name: Optional[str] = None
    provider: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    sample_url: Optional[str] = None
    is_active: Optional[bool] = None


class VoiceModelOut(Schema):
    """Schema for voice model response."""

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
    """Schema for voice model list."""

    items: List[VoiceModelOut]
    total: int


class VoiceProvidersOut(Schema):
    """Schema for available voice providers."""

    providers: List[str]


class VoiceLanguagesOut(Schema):
    """Schema for available voice languages."""

    languages: List[str]

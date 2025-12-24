"""
Voice API endpoints.

Provides REST API for voice persona and model management.
"""
from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import NotFoundError

from .schemas import (
    VoiceLanguagesOut,
    VoiceModelCreate,
    VoiceModelListOut,
    VoiceModelOut,
    VoiceModelUpdate,
    VoicePersonaConfigOut,
    VoicePersonaCreate,
    VoicePersonaListOut,
    VoicePersonaOut,
    VoicePersonaUpdate,
    VoiceProvidersOut,
)
from .services import VoiceModelService, VoicePersonaService

router = Router()


def _persona_to_out(p) -> VoicePersonaOut:
    """Convert VoicePersona model to output schema."""
    return VoicePersonaOut(
        id=p.id,
        tenant_id=p.tenant_id,
        name=p.name,
        description=p.description,
        voice_id=p.voice_id,
        voice_speed=p.voice_speed,
        stt_model=p.stt_model,
        stt_language=p.stt_language,
        llm_provider=p.llm_provider,
        llm_model=p.llm_model,
        system_prompt=p.system_prompt,
        temperature=p.temperature,
        max_tokens=p.max_tokens,
        turn_detection_enabled=p.turn_detection_enabled,
        turn_detection_threshold=p.turn_detection_threshold,
        silence_duration_ms=p.silence_duration_ms,
        is_active=p.is_active,
        is_default=p.is_default,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _model_to_out(m) -> VoiceModelOut:
    """Convert VoiceModel to output schema."""
    return VoiceModelOut(
        id=m.id,
        name=m.name,
        provider=m.provider,
        language=m.language,
        gender=m.gender,
        description=m.description,
        sample_url=m.sample_url,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


# ==========================================================================
# VOICE PERSONA ENDPOINTS
# ==========================================================================
@router.get("/personas", response=VoicePersonaListOut)
def list_personas(
    request,
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List voice personas for current tenant."""
    tenant = request.tenant
    personas, total = VoicePersonaService.list_personas(
        tenant=tenant,
        active_only=active_only,
        page=page,
        page_size=page_size,
    )
    return VoicePersonaListOut(
        items=[_persona_to_out(p) for p in personas],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/personas", response={201: VoicePersonaOut})
def create_persona(request, payload: VoicePersonaCreate):
    """Create a new voice persona."""
    tenant = request.tenant
    persona = VoicePersonaService.create_persona(tenant=tenant, data=payload.dict())
    return 201, _persona_to_out(persona)


@router.get("/personas/default", response=VoicePersonaOut)
def get_default_persona(request):
    """Get the default voice persona for current tenant."""
    tenant = request.tenant
    persona = VoicePersonaService.get_default_persona(tenant)
    if not persona:
        raise NotFoundError("No default voice persona configured")
    return _persona_to_out(persona)


@router.get("/personas/{persona_id}", response=VoicePersonaOut)
def get_persona(request, persona_id: UUID):
    """Get a voice persona by ID."""
    persona = VoicePersonaService.get_persona(persona_id)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    return _persona_to_out(persona)


@router.get("/personas/{persona_id}/config", response=VoicePersonaConfigOut)
def get_persona_config(request, persona_id: UUID):
    """Get voice persona configuration for session use."""
    persona = VoicePersonaService.get_persona(persona_id)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    config = VoicePersonaService.get_persona_config(persona)
    return VoicePersonaConfigOut(**config)


@router.patch("/personas/{persona_id}", response=VoicePersonaOut)
def update_persona(request, persona_id: UUID, payload: VoicePersonaUpdate):
    """Update a voice persona."""
    persona = VoicePersonaService.get_persona(persona_id)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    persona = VoicePersonaService.update_persona(persona, payload.dict(exclude_unset=True))
    return _persona_to_out(persona)


@router.post("/personas/{persona_id}/set-default", response=VoicePersonaOut)
def set_default_persona(request, persona_id: UUID):
    """Set a voice persona as the default."""
    persona = VoicePersonaService.get_persona(persona_id)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    persona = VoicePersonaService.update_persona(persona, {"is_default": True})
    return _persona_to_out(persona)


@router.delete("/personas/{persona_id}", response={204: None})
def delete_persona(request, persona_id: UUID):
    """Delete a voice persona."""
    persona = VoicePersonaService.get_persona(persona_id)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    VoicePersonaService.delete_persona(persona)
    return 204, None


# ==========================================================================
# VOICE MODEL ENDPOINTS
# ==========================================================================
@router.get("/models", response=VoiceModelListOut)
def list_models(
    request,
    provider: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List available voice models."""
    models, total = VoiceModelService.list_models(
        provider=provider,
        language=language,
        active_only=active_only,
    )
    return VoiceModelListOut(
        items=[_model_to_out(m) for m in models],
        total=total,
    )


@router.get("/models/providers", response=VoiceProvidersOut)
def list_providers(request):
    """List available voice providers."""
    providers = VoiceModelService.get_providers()
    return VoiceProvidersOut(providers=providers)


@router.get("/models/languages", response=VoiceLanguagesOut)
def list_languages(request):
    """List available voice languages."""
    languages = VoiceModelService.get_languages()
    return VoiceLanguagesOut(languages=languages)


@router.get("/models/{model_id}", response=VoiceModelOut)
def get_model(request, model_id: str):
    """Get a voice model by ID."""
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    return _model_to_out(model)


@router.post("/models", response={201: VoiceModelOut})
def create_model(request, payload: VoiceModelCreate):
    """Create a new voice model (admin only)."""
    model = VoiceModelService.create_model(payload.dict())
    return 201, _model_to_out(model)


@router.patch("/models/{model_id}", response=VoiceModelOut)
def update_model(request, model_id: str, payload: VoiceModelUpdate):
    """Update a voice model (admin only)."""
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    model = VoiceModelService.update_model(model, payload.dict(exclude_unset=True))
    return _model_to_out(model)


@router.delete("/models/{model_id}", response={204: None})
def delete_model(request, model_id: str):
    """Delete a voice model (admin only)."""
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    VoiceModelService.delete_model(model)
    return 204, None

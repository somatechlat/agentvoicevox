"""
Voice API Endpoints
===================

This module provides the REST API endpoints for managing and interacting with
voice personas and text-to-speech (TTS) voice models. All operations are designed
to be multi-tenant, with data access strictly controlled by the tenant context
of the authenticated user.

Key functionalities include:
- CRUD operations for Voice Personas.
- CRUD operations for Voice Models (partially admin-restricted).
- Endpoints for retrieving configuration and testing voice personas.

The API is built using the Django Ninja framework, which provides automatic
request validation and API documentation generation.
"""

from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import FeatureNotImplementedError, NotFoundError, ValidationError
from apps.llm.services import LLMConfigService
from apps.workflows.activities.llm import LLMActivities, LLMRequest, Message

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
    VoicePersonaTestRequest,
    VoicePersonaTestResponse,
    VoicePersonaUpdate,
    VoiceProvidersOut,
)
from .services import VoiceModelService, VoicePersonaService

router = Router(tags=["Voice"])


def _persona_to_out(p) -> VoicePersonaOut:
    """
    Serializes a VoicePersona Django model instance into a VoicePersonaOut schema.

    This helper function ensures a consistent data structure is returned by the API,
    mapping the model fields to the Pydantic output schema.

    Args:
        p: The VoicePersona model instance.

    Returns:
        A VoicePersonaOut object populated with the persona's data.
    """
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
        solvers=p.solvers,
        usage_count=p.usage_count,
        turn_detection_enabled=p.turn_detection_enabled,
        turn_detection_threshold=p.turn_detection_threshold,
        silence_duration_ms=p.silence_duration_ms,
        is_active=p.is_active,
        is_default=p.is_default,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _model_to_out(m) -> VoiceModelOut:
    """
    Serializes a VoiceModel Django model instance into a VoiceModelOut schema.

    This helper function ensures a consistent data structure is returned by the API,
    mapping the model fields to the Pydantic output schema.

    Args:
        m: The VoiceModel model instance.

    Returns:
        A VoiceModelOut object populated with the model's data.
    """
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
@router.get("/personas", response=VoicePersonaListOut, summary="List Voice Personas")
def list_personas(
    request,
    active_only: bool = Query(False, description="If true, only returns active personas."),
    page: int = Query(1, ge=1, description="The page number for pagination."),
    page_size: int = Query(20, ge=1, le=100, description="The number of items per page."),
):
    """
    Lists all voice personas associated with the current tenant.

    This operation is tenant-scoped. It supports pagination and can optionally
    filter for active personas only.

    Returns:
        A paginated list of voice persona objects.
    """
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


@router.post("/personas", response={201: VoicePersonaOut}, summary="Create a Voice Persona")
def create_persona(request, payload: VoicePersonaCreate):
    """
    Creates a new voice persona for the current tenant.

    This operation is tenant-scoped. The new persona will be owned by the
    tenant of the user making the request.

    Args:
        payload: A VoicePersonaCreate object with the persona's configuration.

    Returns:
        A 201 status code and the newly created voice persona object.
    """
    tenant = request.tenant
    persona = VoicePersonaService.create_persona(tenant=tenant, data=payload.dict())
    return 201, _persona_to_out(persona)


@router.get("/personas/default", response=VoicePersonaOut, summary="Get Default Voice Persona")
def get_default_persona(request):
    """
    Retrieves the default voice persona for the current tenant.

    This operation is tenant-scoped. The default persona is used as a fallback
    when no specific persona is selected for a voice session.

    Returns:
        The default voice persona object for the tenant.

    Raises:
        NotFoundError: If no default persona is configured for the tenant.
    """
    tenant = request.tenant
    persona = VoicePersonaService.get_default_persona(tenant)
    if not persona:
        raise NotFoundError("No default voice persona configured")
    return _persona_to_out(persona)


@router.get("/personas/{persona_id}", response=VoicePersonaOut, summary="Get a Specific Voice Persona")
def get_persona(request, persona_id: UUID):
    """
    Retrieves a specific voice persona by its unique ID.

    This operation is tenant-scoped. Access is restricted to personas
    owned by the current tenant.

    Args:
        persona_id: The UUID of the voice persona to retrieve.

    Returns:
        The requested voice persona object.

    Raises:
        NotFoundError: If the persona does not exist or does not belong to the tenant.
    """
    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    return _persona_to_out(persona)


@router.get(
    "/personas/{persona_id}/config",
    response=VoicePersonaConfigOut,
    summary="Get Persona Configuration for Sessions",
)
def get_persona_config(request, persona_id: UUID):
    """
    Gets the consolidated configuration for a voice persona, intended for voice session use.

    This endpoint aggregates persona settings into a single object that a client
    (like a voice agent) can use to configure its behavior. This operation is
    tenant-scoped.

    Args:
        persona_id: The UUID of the voice persona.

    Returns:
        A configuration object for the specified persona.

    Raises:
        NotFoundError: If the persona does not exist or does not belong to the tenant.
    """
    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    config = VoicePersonaService.get_persona_config(persona)
    return VoicePersonaConfigOut(**config)


@router.patch("/personas/{persona_id}", response=VoicePersonaOut, summary="Update a Voice Persona")
def update_persona(request, persona_id: UUID, payload: VoicePersonaUpdate):
    """
    Updates an existing voice persona.

    This operation is tenant-scoped. Only attributes provided in the payload
    will be updated.

    Args:
        persona_id: The UUID of the voice persona to update.
        payload: A VoicePersonaUpdate object with the fields to modify.

    Returns:
        The updated voice persona object.

    Raises:
        NotFoundError: If the persona does not exist or does not belong to the tenant.
    """
    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    persona = VoicePersonaService.update_persona(persona, payload.dict(exclude_unset=True))
    return _persona_to_out(persona)


@router.post(
    "/personas/{persona_id}/set-default",
    response=VoicePersonaOut,
    summary="Set Persona as Default",
)
def set_default_persona(request, persona_id: UUID):
    """
    Sets a specific voice persona as the default for the current tenant.

    This operation is tenant-scoped. Any existing default will be unset.

    Args:
        persona_id: The UUID of the persona to set as default.

    Returns:
        The updated voice persona object, with `is_default` set to True.

    Raises:
        NotFoundError: If the persona does not exist or does not belong to the tenant.
    """
    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    persona = VoicePersonaService.update_persona(persona, {"is_default": True})
    return _persona_to_out(persona)


@router.delete("/personas/{persona_id}", response={204: None}, summary="Delete a Voice Persona")
def delete_persona(request, persona_id: UUID):
    """
    Deletes a voice persona.

    This operation is tenant-scoped and permanently removes the persona.

    Args:
        persona_id: The UUID of the voice persona to delete.

    Returns:
        A 204 No Content response on successful deletion.

    Raises:
        NotFoundError: If the persona does not exist or does not belong to the tenant.
    """
    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")
    VoicePersonaService.delete_persona(persona)
    return 204, None


@router.post(
    "/personas/{persona_id}/test",
    response=VoicePersonaTestResponse,
    summary="Test a Voice Persona's LLM",
)
async def test_persona(request, persona_id: UUID, payload: VoicePersonaTestRequest):
    """
    Tests a voice persona by sending a message to its configured LLM.

    This endpoint provides a way to quickly verify that the persona's LLM
    configuration (provider, model, system prompt, etc.) is working as expected.
    This operation is tenant-scoped.

    Args:
        persona_id: The UUID of the persona to test.
        payload: A request object containing the test message.

    Returns:
        An object containing the LLM's response text.

    Raises:
        NotFoundError: If the persona is not found.
        ValidationError: If the message is empty.
        FeatureNotImplementedError: If the persona's LLM provider is not supported.
    """
    if not payload.message.strip():
        raise ValidationError("Message is required")

    persona = VoicePersonaService.get_persona(persona_id, tenant=request.tenant)
    if not persona:
        raise NotFoundError(f"Voice persona {persona_id} not found")

    if persona.llm_provider not in {"groq", "openai", "ollama"}:
        raise FeatureNotImplementedError("Unsupported LLM provider")

    secrets = LLMConfigService.read_secrets(request.tenant.id)
    llm_request = LLMRequest(
        tenant_id=str(request.tenant.id),
        session_id=f"persona-test-{persona.id}",
        messages=[Message(role="user", content=payload.message)],
        model=persona.llm_model,
        provider=persona.llm_provider,
        max_tokens=persona.max_tokens,
        temperature=persona.temperature,
        system_prompt=persona.system_prompt,
        api_keys={
            "groq": secrets.get("groq_api_key", ""),
            "openai": secrets.get("openai_api_key", ""),
        },
        ollama_base_url=secrets.get("ollama_base_url", ""),
    )

    result = await LLMActivities().generate_response(llm_request)
    return VoicePersonaTestResponse(response=result.content)


# ==========================================================================
# VOICE MODEL ENDPOINTS
# ==========================================================================
@router.get("/models", response=VoiceModelListOut, summary="List Available Voice Models")
def list_models(
    request,
    provider: Optional[str] = Query(None, description="Filter models by provider (e.g., 'elevenlabs')."),
    language: Optional[str] = Query(None, description="Filter models by language code (e.g., 'en-US')."),
    active_only: bool = Query(True, description="If true, only returns active models."),
):
    """
    Lists all available voice models in the system.

    This operation is not tenant-scoped and shows all public, active models.
    It can be filtered by provider and language.

    Returns:
        A list of available voice model objects.
    """
    models, total = VoiceModelService.list_models(
        provider=provider,
        language=language,
        active_only=active_only,
    )
    return VoiceModelListOut(
        items=[_model_to_out(m) for m in models],
        total=total,
    )


@router.get("/models/providers", response=VoiceProvidersOut, summary="List Voice Providers")
def list_providers(request):
    """
    Lists all unique voice providers available in the system.

    This can be used to populate UI elements for filtering voice models.
    """
    providers = VoiceModelService.get_providers()
    return VoiceProvidersOut(providers=providers)


@router.get("/models/languages", response=VoiceLanguagesOut, summary="List Voice Languages")
def list_languages(request):
    """
    Lists all unique languages available across all voice models.

    This can be used to populate UI elements for filtering voice models.
    """
    languages = VoiceModelService.get_languages()
    return VoiceLanguagesOut(languages=languages)


@router.get("/models/{model_id}", response=VoiceModelOut, summary="Get a Specific Voice Model")
def get_model(request, model_id: str):
    """
    Retrieves a specific voice model by its unique ID.

    This operation is public and not tenant-scoped.

    Args:
        model_id: The ID of the voice model (e.g., 'elevenlabs-Adam').

    Returns:
        The requested voice model object.

    Raises:
        NotFoundError: If the voice model is not found.
    """
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    return _model_to_out(model)


@router.post("/models", response={201: VoiceModelOut}, summary="Create a Voice Model (Admin Only)")
def create_model(request, payload: VoiceModelCreate):
    """
    Creates a new voice model.

    This is an admin-only operation and requires appropriate permissions.

    Args:
        payload: A VoiceModelCreate object with the model's configuration.

    Returns:
        A 201 status code and the newly created voice model object.
    """
    model = VoiceModelService.create_model(payload.dict())
    return 201, _model_to_out(model)


@router.patch("/models/{model_id}", response=VoiceModelOut, summary="Update a Voice Model (Admin Only)")
def update_model(request, model_id: str, payload: VoiceModelUpdate):
    """
    Updates an existing voice model.

    This is an admin-only operation.

    Args:
        model_id: The ID of the voice model to update.
        payload: A VoiceModelUpdate object with the fields to modify.

    Returns:
        The updated voice model object.

    Raises:
        NotFoundError: If the voice model is not found.
    """
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    model = VoiceModelService.update_model(model, payload.dict(exclude_unset=True))
    return _model_to_out(model)


@router.delete("/models/{model_id}", response={204: None}, summary="Delete a Voice Model (Admin Only)")
def delete_model(request, model_id: str):
    """
    Deletes a voice model from the system.

    This is an admin-only operation.

    Args:
        model_id: The ID of the voice model to delete.

    Returns:
        A 204 No Content response on successful deletion.

    Raises:
        NotFoundError: If the voice model is not found.
    """
    model = VoiceModelService.get_model(model_id)
    if not model:
        raise NotFoundError(f"Voice model '{model_id}' not found")
    VoiceModelService.delete_model(model)
    return 204, None
